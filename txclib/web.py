# -*- coding: utf-8 -*-
import urllib2
import itertools, mimetools, mimetypes

# Helper class to enable urllib2 to handle PUT/DELETE requests as well
class RequestWithMethod(urllib2.Request):
    """Workaround for using DELETE with urllib2"""
    def __init__(self, url, method, data=None, headers={},
        origin_req_host=None, unverifiable=False):
        self._method = method
        urllib2.Request.__init__(self, url, data=data, headers=headers,
                 origin_req_host=None, unverifiable=False)

    def get_method(self):
        return self._method

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.formFields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()

    def getContentType(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def addField(self, name, value):
        """Add a form field to the form data."""

        self.formFields.append((name, value))

    def addFile(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""

        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        self.files.append((fieldname, filename, mimetype, body))

    def __str__(self):
        """Return a string representing the form data, including attached files."""

        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # refer http://www.ietf.org/rfc/rfc2388.txt (RFC2388)

        parts = []
        partBoundary = '--' + self.boundary

        # Add the form fields

        parts.extend([ partBoundary,'Content-Disposition: form-data; name="%s"' %
        name,\
            '', value,] for name, value in self.formFields)

        # Add the files to upload
        # Amazon S3 expects file data to be 'Content-Disposition:
        # form-data' instead of "file"

        parts.extend([ partBoundary,'Content-Disposition: form-data; name="%s"; filename="%s"' % \
            (fieldName, filename),'Content-Type: %s' % contentType,'',body,]
            for fieldName, filename, contentType, body in self.files)

        # Flatten the list and add closing boundary marker,
        # then return \r\n separated data

        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)


