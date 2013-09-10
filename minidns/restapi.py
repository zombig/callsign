from zope.interface import implements
from twisted.application import internet
from twisted.web.server import Site
from twisted.web.resource import Resource, NoResource

class RecordResource(Resource):

    def __init__(self, name, zone):
        Resource.__init__(self)
        self.name = name
        self.zone = zone

    def render_PUT(self, request):
        data = request.content.read()
        self.zone.set_record(self.name, data)
        request.setResponseCode(201)
        return ""

    def render_DELETE(self, requests):
        self.zone.delete_record(self.name)
        request.setResponseCode(204)
        return ""

class DomainResource(Resource):

    def __init__(self, zone):
        Resource.__init__(self)
        self.zone = zone

    def render_GET(self, request):
        import wingdbstub
        l = []
        for name, value in self.zone.a_records():
            l.append("%s %s" % (name, value))
        return "\n".join(l)

    def getChild(self, path, request):
        return RecordResource(path, self.zone)

class MissingDomainResource(Resource):

    """ A resource that can only be PUT to to create a new zone """

    def __init__(self, name, factory):
        Resource.__init__(self)
        self.name = name
        self.factory = factory

    def render_PUT(self, request):
        self.factory.add_zone(self.name)
        request.setResponseCode(201)
        return ""

class RootResource(Resource):

    def __init__(self, config, dnsserver):
        Resource.__init__(self)
        self.config = config
        self.dnsserver = dnsserver

    def render_GET(self, request):
        return "\n".join(self.dnsserver.zones())

    def getChild(self, path, request):
        if path == "":
            return self
        path = path.rstrip(".")
        try:
            zone = self.dnsserver.get_zone(path)
            return DomainResource(zone)
        except KeyError:
            return MissingDomainResource(path, self.dnsserver.factory)

def webservice(config, dnsserver):
    root = RootResource(config, dnsserver)
    site = Site(root)
    return internet.TCPServer(config['www_port'], site)
