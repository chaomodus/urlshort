#
# urlshort_app - a cherrypy application mapping urlshort to web.
# by Cas Rusnov <rusnovn@gmail.com>
#

import jinja2
import cherrypy
import re
import sys
import ConfigParser
import urlshort

# this regexp scares me. -cas
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
    """Maps the /tag/ namespace."""
    def __init__(self, shortener, jinjaenv):
        self.shortener = shortener
        self.jinjaenv = jinjaenv

    def _cp_dispatch(self, vpath):
        """support /tag/<tagname>"""
        if len(vpath) == 1:
            cherrypy.request.params['tagname'] = vpath.pop(0)
            return self
        return vpath

    @cherrypy.expose
    def index(self, tagname=''):
        if tagname:
            # if a tag name is specified, list URLs with that tag.
            urls = self.shortener.get_urls_by_tag(tagname)
            [url.append(cherrypy.request.base + '/' + url[0]) for url in urls]
            templ = self.jinjaenv.get_template('tagurls.html')
            return templ.render(urls=urls, tag=tagname)
        else:
            # default - show tag cloud
            tags = self.shortener.get_tags()
            maxcount = float(max([x[1] for x in tags]))
            templ = self.jinjaenv.get_template('tagcloud.html')
            return templ.render(tags=tags, maxcount=maxcount)

class URLDetails(object):
    """Maps the /details/ namespace."""
    def __init__(self, shortener, jinjaenv):
        self.shortener = shortener
        self.jinjaenv = jinjaenv

    def _cp_dispatch(self, vpath):
        """Support /details/<urlid>"""
        if len(vpath) == 1:
            cherrypy.request.params['urlcode'] = vpath.pop(0)
            return self

        return vpath

    @cherrypy.expose
    def index(self, urlcode=''):
        if urlcode:
            # if a urlid is specified, show a details page for URL.
            details = self.shortener.get_url_details(urlcode)
            if details:
                shorturl = cherrypy.request.base + '/' + urlcode
                templ = self.jinjaenv.get_template('details.html')
                return templ.render(details=details, shorturl = shorturl)
            raise cherrypy.NotFound()
        else:
            # default - show full URL list.
            # fixme add pagination
            urls = self.shortener.get_urls_details()
            [url.append(cherrypy.request.base + '/' + url[0]) for url in urls]
            templ = self.jinjaenv.get_template('detailurls.html')
            return templ.render(urls=urls)

class URLShortApp(object):
    """Handle / namespace."""
    def __init__(self, shortener, jinjaenv):
        self.shortener = shortener
        self.jinjaenv = jinjaenv

    def _cp_dispatch(self, vpath):
        """Support /<urlid>"""
        if vpath[0] not in ('tags','new','details'):
            cherrypy.request.params['urlcode'] = vpath.pop(0)
            return self

        return vpath

    @cherrypy.expose
    def index(self,urlcode=''):
        if urlcode:
            # if a url is specified, redirect
            url = self.shortener.get_url(urlcode)
            if url:
                raise cherrypy.HTTPRedirect(url)
            else:
                raise cherrypy.NotFound()
        else:
            # default - show the front page / creation form
            return self.jinjaenv.get_template('newform.html').render()

    @cherrypy.expose
    def new(self, url, tags):
        """Handle a new URL creation."""
        m = URL_REGEX.match(url)
        if m:
            # prepend http:// if no scheme is present.
            if not m.groups()[0]:
                url = 'http://' + url
            #messy
            raise cherrypy.HTTPRedirect('/details/'+self.shortener.add_url(url, [tag.strip() for tag in tags.split(',')]))
        else:
            return self.jinjaenv.get_template('newform.html').render(message="Invalid URL")

if __name__ == '__main__':
    # load default configuration
    config = ConfigParser.ConfigParser()
    config.readfp(file('urlshort.ini','r'))
    # load user configurations
    if len(sys.argv) > 1:
        for conf in sys.argv[1:]:
            config.read(conf)

    # hypothetically we can have cherrypy load the ini files and handle this
    cherrypy.config.update({'server.socket_port':config.getint('global','socketport')})
    cherrypy.config.update({'server.socket_host':config.get('global','sockethost')})
    cherrypy.config.update({'environment':config.get('global','environment')})

    # fixme allow template folders to be configured
    jinjaenv = jinja2.Environment(loader=jinja2.FileSystemLoader('./templates'))
    jinjaenv.filters['isotime'] = isotime

    # map configuration options to DSN.
    myshortener = urlshort.URLShort(database=config.get('database','database'), user=config.get('database','user'), password=config.get('database','password'), host=config.get('database','host'), port=config.getint('database','port'))
    cherrypy.tree.mount(URLTags(myshortener, jinjaenv), '/tags/')
    cherrypy.tree.mount(URLDetails(myshortener, jinjaenv), '/details/')
    cherrypy.quickstart(URLShortApp(myshortener, jinjaenv), '/')
