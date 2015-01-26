import jinja2
import cherrypy
import re
import sys
import ConfigParser
import urlshort

URL_REGEX = re.compile(
    u"^"
    # protocol identifier
    u"((?:https?|ftp)://)?"
    # user:pass authentication
    u"(?:\S+(?::\S*)?@)?"
    u"(?:"
    # IP address exclusion
    # private & local networks
    u"(?!(?:10|127)(?:\.\d{1,3}){3})"
    u"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
    u"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
    # IP address dotted notation octets
    # excludes loopback network 0.0.0.0
    # excludes reserved space >= 224.0.0.0
    # excludes network & broadcast addresses
    # (first & last IP address of each class)
    u"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
    u"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
    u"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
    u"|"
    # host name
    u"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
    # domain name
    u"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
    # TLD identifier
    u"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
    u")"
    # port number
    u"(?::\d{2,5})?"
    # resource path
    u"(?:/\S*)?"
    # form arguments
    u"(?:\?\S+)?"
    u"$"
    , re.UNICODE)

def isotime(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S%z')

class URLTags(object):
    def __init__(self, shortener, jinjaenv):
        self.shortener = shortener
        self.jinjaenv = jinjaenv

    def _cp_dispatch(self, vpath):
        if len(vpath) == 1:
            cherrypy.request.params['tagname'] = vpath.pop(0)
            return self
        return vpath

    @cherrypy.expose
    def index(self, tagname=''):
        if tagname:
            urls = self.shortener.get_urls_by_tag(tagname)
            [url.append(cherrypy.request.base + '/' + url[0]) for url in urls]
            templ = self.jinjaenv.get_template('tagurls.html')
            return templ.render(urls=urls, tag=tagname)
        else:
            tags = self.shortener.get_tags()
            maxcount = float(max([x[1] for x in tags]))
            templ = self.jinjaenv.get_template('tagcloud.html')
            return templ.render(tags=tags, maxcount=maxcount)

class URLDetails(object):
    def __init__(self, shortener, jinjaenv):
        self.shortener = shortener
        self.jinjaenv = jinjaenv

    def _cp_dispatch(self, vpath):
        if len(vpath) == 1:
            cherrypy.request.params['urlcode'] = vpath.pop(0)
            return self

        return vpath

    @cherrypy.expose
    def index(self, urlcode=''):
        if urlcode:
            details = self.shortener.get_url_details(urlcode)
            if details:
                shorturl = cherrypy.request.base + '/' + urlcode
                templ = self.jinjaenv.get_template('details.html')
                return templ.render(details=details, shorturl = shorturl)
            raise cherrypy.NotFound()
        else:
            urls = self.shortener.get_urls_details()
            [url.append(cherrypy.request.base + '/' + url[0]) for url in urls]
            templ = self.jinjaenv.get_template('detailurls.html')
            return templ.render(urls=urls)

class URLShortApp(object):
    def __init__(self, shortener, jinjaenv):
        self.shortener = shortener
        self.jinjaenv = jinjaenv

    def _cp_dispatch(self, vpath):
        if vpath[0] not in ('tags','new','details'):
            cherrypy.request.params['urlcode'] = vpath.pop(0)
            return self

        return vpath

    @cherrypy.expose
    def index(self,urlcode=''):
        if urlcode:
            url = self.shortener.get_url(urlcode)
            if url:
                raise cherrypy.HTTPRedirect(url)
            else:
                raise cherrypy.NotFound()
        else:
            return self.jinjaenv.get_template('newform.html').render()

    @cherrypy.expose
    def new(self, url, tags):
        m =URL_REGEX.match(url)
        if m:
            if not m.groups()[0]:
                url = 'http://' + url
            #messy
            raise cherrypy.HTTPRedirect('/details/'+self.shortener.add_url(url, [tag.strip() for tag in tags.split(',')]))
        else:
            return self.jinjaenv.get_template('newform.html').render(message="Invalid URL")

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(file('urlshort.ini','r'))
    if len(sys.argv) > 1:
        for conf in sys.argv[1:]:
            config.read(conf)

    cherrypy.config.update({'server.socket_port':config.getint('global','socketport')})
    cherrypy.config.update({'environment':config.get('global','environment')})

    jinjaenv = jinja2.Environment(loader=jinja2.FileSystemLoader('./templates'))
    jinjaenv.filters['isotime'] = isotime
    myshortener = urlshort.URLShort(database=config.get('database','database'), user=config.get('database','user'), password=config.get('database','password'), host=config.get('database','host'), port=config.getint('database','port'))
    cherrypy.tree.mount(URLTags(myshortener, jinjaenv), '/tags/')
    cherrypy.tree.mount(URLDetails(myshortener, jinjaenv), '/details/')
    cherrypy.quickstart(URLShortApp(myshortener, jinjaenv), '/')
