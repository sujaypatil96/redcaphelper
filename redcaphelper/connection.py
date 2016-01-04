"""
A live connection to a REDCap database.

This serves largely to wrap associated functionality around a PyCap connection,
mostly just for neatness.
"""

### IMPORTS

import redcap

import .const
import .utils

__all__ = [
	'Connection'
]


### CONSTANT & DEFINES

### CODE ###

class Connection (object):
	"""
	A live connection to a REDCap database.

	Mostly just a wrapping of the PyCap interface, for neatness.
	"""

	def __init__ (self, url, token):
		"""
		Initialise connection to REDCap project.

		Args:
			url (str): URL of the database
			token (str): the long alphanumeric access string. Note that this is
				specific to a database and a user (and that user's permissions).

		For example::

			>>> import os
			>>> url = os.environ['REDCAPHELPER_TEST_URL']
			>>> token = os.environ['REDCAPHELPER_TEST_TOKEN']
			>>> conn = Connection (url, token)

		"""
		## Preconditions:
		assert url.startswith ('http'), \
			"redcap api url '%s' is deformed " % url
		assert url.endswith ('/'), \
			"redcap api url '%s' does not end in forward-slash" % url

		## Main:
		self._proj = redcap.Project (url, token)

	def import_recs (self, recs, chunk_sz=consts.DEF_UPLOAD_CHUNK_SZ,
			sleep=consts.DEF_SLEEP, overwrite=True):
		"""
		Import records into the attached database.

		Args:
			recs (sequence of dicts): data to be uploaded
			chunk_sz (int): number of records to be uploaded in each batch
			sleep (int): seconds to wait between each upload
			overwrite (bool): should values missing in the import be overwritten

		Importing is a memory- (and CPU-) hungry process for REDCap. Thus it is
		necessary to manually throttle the process by uploading data in chunks
		and pausing between chunks.

		"""
		# TODO(paul): exactly what does the overwrite arg do?
		# TODO(paul): print better response & handle reponses better
		# TODO(paul): have seperate upload_chunk function for better handling?
		# TODO(paul): need date format option?

		total_len = len (recs)
		for x in range (0, total_len, chunk_sz):
			start = x
			stop = min (total_len, x+chunk_sz)
			self.print_progress ("Uploading records %s-%s of %s" % (start, stop-1, total_len))
			response = self._proj.import_records (
				recs[start:stop],
				overwrite='overwrite' if overwrite else 'normal'
			)
			self._print_progress (response)
			if sleep and (stop != total_len):
				time.sleep (sleep)

	def export_recs (self, chunk_sz=consts.DEF_DOWNLOAD_CHUNK_SZ, flds=None):
		"""
		Download data in chunks to avoid memory errors.

		Args:
			chunk_sz (int): number of records to be downloaded in each batch
			flds (sequence): a list of the fields to be exported

		Exporting is also a memory-hungry process for REDCap. Thus we make it
		easy on the server by batching up the downloaded records and combining
		them ourselves.

		"""
		# TODO(paul): allow setting of format?
		# TODO(paul): combine chunking functions?

		## Preconditions & preparation:
		flds = flds or self._proj.def_field

		## Main:
		def chunks(l, n):
			"""
			Yield successive n-sized chunks from list l
			"""
			for i in range (0, len(l), n):
				yield l[i:i+n]

		id_fld = self._proj.def_field
		record_list = self._proj.export_records (fields=[id_fld])
		records = [r[id_fld] for r in record_list]

		try:
			response = []
			for record_chunk in chunks (records, chunk_sz):
				chunked_response = project.export_records (records=record_chunk)
				response.extend (chunked_response)
		except redcap.RedcapError:
			msg = "Chunked export failed for chunk_size={:d}".format (chunk_sz)
			raise ValueError (msg)
		else:
			return response

	def export_schema (self):
		"""
		Download the project schema (fields).

		The project object actually contains the project schema as metadata
		but in a slightly awkward format. This returns the schema as a series of
		dicts giving the fields and their various options like validation.

		These will be in the order they appear in the project.

		"""
		csv_txt = self._proj.export_metadata (format='csv')
		csv_rdr = csv.DictReader (io.StringIO (csv_txt))
		return [r for r in csv_rdr]

	def export_field_names (self):
		"""
		Download the project fields.

		These will be in the order they appear in the project. Remember that in
		REDCap, IDs are "names" and titles are "labels".

		"""
		return [r['Variable / Field Name'] for r in self.export_schema()]

	def _print_progress (self, msg):
		"""
		Print some diagnostic messages showing that things are happening.

		"""
		# XXX: this is balls, probably needs to be replaced with decent messaging
		print (msg, '...')



### END ###
