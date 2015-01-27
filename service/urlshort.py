#
# urlshort - a simple database model for URL shortening / bookmarking.
# written by Cas Rusnov <rusnovn@gmail.com>
#
import pg8000
import baseconvert
import datetime

# an alphabet which minimizes ambiguous / lookalike characters while remaining URL safe.
URLSHORT_ALPHABET = "ab2c3d4e5f6g7h8i9AjBkCmDnEoFpGqHrJsKtLuMvNwOxPyQzR~S!T@U#V$W^X*Y(Z)][-"
pg8000.paramstyle = 'qmark'

class URLShort(object):
    def __init__(self, **pgopts):
        self.pgopts = pgopts
        self._db = pg8000.connect(**pgopts)
        curs = self._db.cursor()
        curs.execute("""SELECT id FROM users WHERE name='anonymous'""")
        self.anonyid = curs.fetchone()[0]

    def add_url(self, url, tags=[], creator=None):
        """add a URL to the database

        returns the encoded id of the URL.
        """
        cursor = self._db.cursor()
        cursor.execute('SELECT id FROM urls WHERE uri=?', (url,))
        if cursor.rowcount:
            return self.encode_id(cursor.fetchone()[0])

        cursor.execute("""INSERT INTO urls (uri, owner, created) VALUES (?, ?, now()) RETURNING id""", (url, self.anonyid, tags))
        urlid = cursor.fetchone()[0]
        for tag in tags:
            cursor.execute("""INSERT INTO tags (tag, url) VALUES (?, ?)""", (tag, urlid))
        self._db.commit()
        return self.encode_id(urlid)

    def get_url(self, idcode):
        """retrieve a single URL from the database by id

        idcode: the encoded id of the URL.

        returns just the URL.
        """
        cursor = self._db.cursor()
        cursor.execute("""SELECT uri FROM urls WHERE id=?""", (self.decode_id(idcode),))
        if cursor.rowcount:
            return cursor.fetchone()[0]

    def get_urls_details(self):
        """Get the full record of all URLs from the database

        returns a list of lists containing [urlid, uri, creator, created timestamp, [tags]]
        """
        cursor = self._db.cursor()
        cursor.execute("""SELECT urls.id, urls.uri, users.name, urls.created, ARRAY(SELECT tag FROM tags WHERE  url=urls.id) FROM urls, users WHERE urls.owner = users.id""")
        res = list()
        for url in cursor.fetchall():
            res.append(list(url))
            res[-1][0] = self.encode_id(res[-1][0])
        return res

    def get_url_details(self, idcode):
        """Get the full details of a particular URL by id.

        idcode: the encoded id of the URL.

        returns a list containinng [urlid, uri, creator, created timestamp, [tags]
        """
        cursor = self._db.cursor()
        cursor.execute("""SELECT urls.id, urls.uri, users.name, urls.created, ARRAY(SELECT tag FROM tags WHERE  url=urls.id) FROM urls, users WHERE urls.id=? AND urls.owner = users.id""", (self.decode_id(idcode),))
        if cursor.rowcount:
            val = list(cursor.fetchone())
            val[0] = self.encode_id(val[0])
            return val

    def get_tags(self):
        """Get the list of unique tags in the database.

        returns a list of [tag, count]
        """
        cursor = self._db.cursor()
        cursor.execute("""SELECT tag, count(*) FROM tags GROUP BY tag""")
        return list(cursor.fetchall())

    def get_urls_by_tag(self, tag):
        """Get a list of URLs by tag.

        tag: a tag string.

        returns a list of [urlid, uri, creaator, created timestamp]
        """
        cursor = self._db.cursor()
        cursor.execute("""SELECT urls.id, urls.uri, users.name, urls.created FROM urls, users WHERE urls.id in (SELECT url FROM tags WHERE tag=?) AND urls.owner = users.id""", (tag,))
        val = list()
        for row in cursor.fetchall():
            val.append(list(row))
            val[-1][0] = self.encode_id(val[-1][0])
        return val

    def encode_id(self, idnr):
        """Encode a number using the shortener alphabet.

        idnr: a positive integer.

        retruns encoded string.
        """
        return baseconvert.baseN_encode(idnr, URLSHORT_ALPHABET)

    def decode_id(self, idcode):
        """Decode an encoded string into a number.

        idcode: an encoded string.

        returns a positive integer.
        """
        return baseconvert.baseN_decode(idcode, URLSHORT_ALPHABET)
