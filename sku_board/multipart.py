"""Lossless UTF-8 form fields on the existing streaming CGI upload path."""
import cgi


class ByteFieldStorage(cgi.FieldStorage):
    def read_lines(self):
        # FieldStorage otherwise decodes each 64 KiB readline independently.
        # A multi-byte character crossing that boundary becomes replacement chars.
        # Keep field bodies as bytes (including temporary-file spillover) and decode
        # once in the handler. Headers/filenames retain CGI's normal UTF-8 parsing.
        self._binary_file = True
        super().read_lines()
