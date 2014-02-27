import os
import sublime_plugin
import sublime
import subprocess
import re

settingsfile = "Stata Enhanced.sublime-settings"

def strip_inline_comments(text):
  # This is really brute force and hackish. Ideally we could use ST scopes to
  # only remove comments instead of trying to parse everything with regex
  # (since there will inevitably be edge cases that should/shouldn't be
  # removed). ST kind of has that functionality: 
	# 	self.view.find_by_selector('comment')
	# But this is a good stopgap for now.
  clean = text

  # Take care of line continuation
  clean = re.sub("/{3,}\\n", "", clean)

  # Remove /* ... */ comments (handles multiple lines)
  # Inscrutable regex courtesy of http://ostermiller.org/findcomment.html
  clean = re.sub("/\\*([^*]|[\\r\\n]|(\\*+([^*/]|[\\r\\n])))*\\*+/", "", clean)

  # Remove // comments
  clean = re.sub("//(.*)\\n", "", clean)

  return(clean)


class text_2_stata13Command(sublime_plugin.TextCommand):
	""" Run selection or current line *directly* in Stata (for Stata 13) """

	def run(self, edit):
		settings = sublime.load_settings(settingsfile)

		# Get the selection; if nothing is selected, get the current line
		all_text = ""
		sels = self.view.sel()
		for sel in sels:
			all_text = all_text + self.view.substr(sel)
		if len(all_text) == 0:
			all_text = self.view.substr(self.view.line(sel)) 
		all_text = all_text + "\n"

		# Get rid of inline comments
		all_text = strip_inline_comments(all_text)

		# Send the command to Stata with AppleScript
		cmd = """osascript<< END
		 tell application "{0}"
			# activate
			DoCommandAsync "{1}" with addToReview
		 end tell
		 END""".format(settings.get('stata_name'), all_text.replace('"', '\\"').replace('`', '\\`').strip()) 
		print(cmd)
		os.system(cmd)


class text_2_stataCommand(sublime_plugin.TextCommand):
	""" Run selection or current line in Stata through a temporary file (for Stata < 13) """
	def run(self, edit):
		# Get the selection; if nothing is selected, get the current line
		all_text = ""
		sels = self.view.sel()
		for sel in sels:
			all_text = all_text + self.view.substr(sel)
		if len(all_text) == 0:
			all_text = self.view.substr(self.view.line(sel)) 
		all_text = all_text + "\n"

		# Get rid of inline comments
		all_text = strip_inline_comments(all_text)

		# Get the path to the current rile
		filename = self.view.file_name()
		filepath = os.path.dirname(filename)

		# Write the selection to a temporary file in the current directory
		dofile_path = os.path.join(filepath, 'sublime2stata.do')
		this_file = open(dofile_path,'w')
		this_file.write(all_text)
		this_file.close()

		# Open the temporary do file in Stata
		cmd = """osascript -e 'tell application "Finder" to open POSIX file "{0}"' &""".format(dofile_path)
		os.system(cmd)
