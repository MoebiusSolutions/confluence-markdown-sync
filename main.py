from atlassian import Confluence
import os
from pathlib import Path
import argparse
import json
import subprocess
import hashlib
from multiprocessing import Pool
import jinja2

# A version of argparse.ArgumentParser, that report errors
# with a non-zero exit code
class WrappedArgumentParser(argparse.ArgumentParser):
	def error(self, message):
		self.exit(125, '%s: error: %s\n' % (self.prog, message))

def _parse_args_or_exit():
	parser = WrappedArgumentParser(description='A utility for pushing a markdown wiki to confluence.')
	parser.add_argument('--config', metavar=('<config-file>'), required=True, help='List of one or more config files that are merged (latter having precedence).')
	args_config = parser.parse_args()
	return _load_json_with_comments(args_config.config)

def _load_json_with_comments(json_file):
	with open(json_file, 'r') as in_file:
		# Load config file, stripping off comments
		json_lines = []
		for line in in_file:
				li=line.strip()
				if li.startswith('//'):
						json_lines.append('')
				else:
						json_lines.append(line)
		return json.loads(''.join(json_lines))

def _get_markdown_files(source_dir):
	markdown_files=[]
	for filename in os.listdir(source_dir):
		if not filename.endswith('.md'):
			continue
		markdown_files.append(filename)
	markdown_files.sort()
	return markdown_files

def _dump_confluence_pages_to_json(confluence, confluence_space, parent_page_id, out_file):
	child_pages = []
	start_record = 0
	limit_records = 100
	while True:
		had_result = False
		for child in confluence.get_page_child_by_type(
			parent_page_id, type='page', start=start_record, limit=limit_records, expand="body"):
			had_result = True
			child_pages.append({"Parent id": parent_page_id, "Id": child["id"], "Title": child["title"]})
		if not had_result:
			break
		start_record += limit_records
	with open(out_file, 'w') as f:
		json.dump(child_pages, f, indent=2)

def _get_confluence_child_pages(page_list_dump_file, parent_page_id):
	with open(page_list_dump_file, 'r') as f:
		child_pages = json.load(f)
	result = []
	for child_page in child_pages:
		# Skip any pages not immediate children (including the parent page itself)
		if str(child_page['Parent id']) != parent_page_id:
			continue
		result.append(child_page)
	return result

def _process_markdown_file(confluence, confluence_space, parent_page_id, page_template, source_dir, state_dir, markdown_filename, update_confluence_page):

	markdown_file = source_dir/markdown_filename
	temp_content_file = state_dir/(markdown_filename+'.confluence')
	markdown_hash_file = state_dir/(markdown_filename+'.lastSynced')

	# Generate the content for Confluence
	_generate_confluence_content(
		markdown_file, temp_content_file, page_template)

	# Read file hashes
	new_markdown_hash = _read_hash(temp_content_file)
	previous_markdown_hash = ''
	if markdown_hash_file.exists():
		with open(markdown_hash_file, 'r') as f:
			previous_markdown_hash = f.read()

	# Stop if content hasn't changed
	if new_markdown_hash == previous_markdown_hash:
		print('Skipping (already synced): '+markdown_filename)
		return
	else:
		print('Updating: '+markdown_filename)

	# Update the page
	update_confluence_page(
		confluence,
		parent_page_id,
		confluence_space,
		markdown_filename,
		temp_content_file)

	# Store the last-synced hash
	with open(markdown_hash_file, 'w') as f:
		f.write(new_markdown_hash)

def _generate_confluence_content(markdown_file, confluence_file, page_template):
	markdown_content = ""
	with open(markdown_file, 'r') as in_file:
		markdown_content = in_file.read()
	with open(page_template, 'r') as f:
		template = jinja2.Template(f.read())
	with open(confluence_file, 'w') as f:
		f.write(template.render(markdown_filename=markdown_file.name, markdown_content=markdown_content))

def _update_confluence_page_by_id(confluence, page_id, title, content_file):
	content = ""
	with open(content_file, 'r') as f:
		content = f.read()
	confluence.update_page(page_id, title, content, representation='storage')

def _update_confluence_page_as_child(confluence, confluence_space, parent_id, title, content_file):
	content = ""
	with open(content_file, 'r') as f:
		content = f.read()
	confluence.update_or_create(parent_id, title, content, representation='storage')

def _delete_confluence_page(confluence, page_id, page_title):
	print('Deleting: '+page_title)
	confluence.remove_page(page_id, status=None, recursive=False)

def _exec(cmd):
	print("Executing: %s" % cmd)
	subprocess.run(cmd,
			stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,
			check=True)

def _read_hash(file):
	with open(file,"rb") as f:
		sha256_hash = hashlib.sha256()
		for byte_block in iter(lambda: f.read(4096),b""):
			sha256_hash.update(byte_block)
		return sha256_hash.hexdigest()

def join_throwing_any_exception(worker_pool, jobs):
	worker_pool.close()
	# Check for exceptions on any jobs (as soon as possible--before join)
	for job in jobs:
		job.get()
	worker_pool.join()

# This would be an in-line lambda, if multiprocessing could use one
def _lambda_update_confluence_page_as_child(confluence, parent_page_id, confluence_space, markdown_filename, temp_content_file):
	_update_confluence_page_as_child(confluence, confluence_space, parent_page_id, markdown_filename, temp_content_file)

def _main():
	config = _parse_args_or_exit()
	source_dir = Path(config['markdown_dir'])
	state_dir = Path(config['state_dir'])

	print('')
	print('[[ Identifying Markdown Files ]]')

	# Read markdown file list
	markdown_files = sorted(_get_markdown_files(source_dir))
	markdown_files_set = set(markdown_files)

	print('')
	print('[[ Pushing Pages to Confluence ]]')
	print('')
	
	confluence = Confluence(url=config['confluence_url'], token=config['confluence_token'])

	# Update README.md
	_process_markdown_file(
		confluence,
		config['confluence_space'],
		config['parent_page_id'],
		config['page_template'],
		source_dir,
		state_dir, 
		'README.md',
		lambda confluence, parent_page_id, confluence_space, markdown_filename, temp_content_file:
			_update_confluence_page_by_id(confluence, parent_page_id, config['root_page_title'], temp_content_file))

	# Create/update all other .md files
	worker_pool = Pool(processes=config['confluence_threads'])
	jobs = []
	for markdown_filename in markdown_files:
		job = worker_pool.apply_async(_process_markdown_file, [
			confluence,
			config['confluence_space'],
			config['parent_page_id'],
			config['page_template'],
			source_dir,
			state_dir,
			markdown_filename,
			_lambda_update_confluence_page_as_child])
		jobs.append(job)
	join_throwing_any_exception(worker_pool, jobs)

	print('')
	print('[[ Reading Page List from Confluence ]]')
	print('')

	# Read confluence page list
	page_list_dump_file = state_dir/'page_list_dump.json'
	_dump_confluence_pages_to_json(
		confluence,
		config['confluence_space'],
		config['parent_page_id'],
		page_list_dump_file)
	confluence_child_pages = _get_confluence_child_pages(page_list_dump_file, config['parent_page_id'])

	print('')
	print('[[ Pruning Deleted Pages from Confluence ]]')
	print('')

	# Delete any confluence pages that do not exist as markdown files
	for confluence_child_page in confluence_child_pages:
		# NOTE: We prune 'README.md' as well, since this is the parent page's content
		if (confluence_child_page['Title'] == 'README.md') or (confluence_child_page['Title'] not in markdown_files_set):
			_delete_confluence_page(
				confluence,
				str(confluence_child_page['Id']),
				confluence_child_page['Title'])

	print('')
	print('[[ Complete ]]')
	print('')

_main()
