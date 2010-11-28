import ConfigParser

class OrderedRawConfigParser( ConfigParser.RawConfigParser ):
    """
    Overload standard Class ConfigParser.RawConfigParser
    """
    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            for key in sorted( self._defaults ):
                fp.write( "%s = %s\n" % (key, str( self._defaults[ key ]
                    ).replace('\n', '\n\t')) )
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for key in sorted( self._sections[section] ):
                if key != "__name__":
                    fp.write("%s = %s\n" %
                        (key, str( self._sections[section][ key ]
                        ).replace('\n', '\n\t')))
            fp.write("\n")

    optionxform = str

