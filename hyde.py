#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse
import os
import sys

import hydeengine

PROG_ROOT = os.path.dirname(os.path.realpath( __file__ ))

def main():
    parser = optparse.OptionParser(usage="%prog [-f] [-q]", version="%prog 0.5.3")
    parser.add_option("-s", "--sitepath",
                        dest = "site_path",
                        help = "Change the path of the site folder.")
    parser.add_option("-i", "--init", action = 'store_true',
                        dest = "init", default = False,
                        help = "Create a new hyde site.")
    parser.add_option("-f", "--force", action = 'store_true',
                        dest = "force_init", default = False, help = "")
    parser.add_option("-t", "--template",
                        dest = "template",
                        help = "Choose which template you want to use.")
    parser.add_option("-g", "--generate", action = "store_true",
                        dest = "generate", default = False,
                        help = "Generate the source for your hyde site.")
    parser.add_option("-k", "--keep_watching", action = "store_true",
                        dest = "keep_watching", default = False,
                        help = "Start monitoring the source folder for changes.")
    parser.add_option("-d", "--deploy_to",
                        dest = "deploy_to",
                        help = "Change the path of the deploy folder.")
    parser.add_option("-w", "--webserve", action = "store_true",
                        dest = "webserve", default = False,
                        help = "Start serving using a webserver.")
    parser.add_option("--web-flavor", metavar='NAME', default="CherryPy", help="Specify the flavor of the server (CherryPy, gevent)")
    parser.add_option("--settings", default="settings", help="Specify the settings file name to be used")
    parser.add_option("-p", "--port",
                        dest = "port", default=8080,
                        type='int',
                        help = "Port webserver should listen on (8080).")
    parser.add_option("-a", "--address",
                        dest = "address", default='localhost',
                        help = "Address webserver should listen on (localhost).")

    (options, args) = parser.parse_args()

    if len(args):
        parser.error("Unexpected arguments encountered.")

    if options.webserve:
        servers = {'cherrypy': hydeengine.Server,
                   'gevent':   hydeengine.GeventServer}

        Server = servers.get(options.web_flavor.lower())
        if not Server:
            parser.error('Invalid web service flavor "%s" (valid: %s)' % \
                         (options.web_flavor, ', '.join(servers.keys())))


    if not options.site_path:
        options.site_path = os.getcwdu()

    if options.deploy_to:
        options.deploy_to = os.path.abspath(options.deploy_to)

    if options.init:
        initializer = hydeengine.Initializer(options.site_path)
        initializer.initialize(PROG_ROOT,
                        options.template, options.force_init)

    generator = None
    server = None

    def quit(*args, **kwargs):
        if server and server.alive:
            server.quit()
        if generator:
            generator.quit()

    if options.generate:
        generator = hydeengine.Generator(options.site_path)
        generator.generate(options.deploy_to, options.keep_watching, quit, options.settings)

    if options.webserve:
        server = Server(options.site_path, address=options.address, port=options.port)
        server.serve(options.deploy_to, quit, options.settings)

    if ((options.generate and options.keep_watching)
                    or
                    options.webserve):
        try:
            print "Letting the server and/or the generator do their thing..."
            if server:
                server.block()
                if generator:
                    generator.quit()
            elif generator:
                generator.block()
        except:
            print sys.exc_info()
            quit()

    if len(sys.argv) == 1:
        print parser.format_option_help()


if __name__ == "__main__":
    main()
    # import cProfile
    # cProfile.run('main(sys.argv[1:])', filename='hyde.cprof')
    # import pstats
    # stats = pstats.Stats('hyde.cprof')
    # stats.strip_dirs().sort_stats('time').print_stats(20)
