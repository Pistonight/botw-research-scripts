import os
import util as u
import task as t

if __name__ == "__main__":
    output = u.output(".")
    if not os.path.exists(output):
        os.makedirs(output)

    mgr = t.mgr()
    from tasks import link_actors
    u.fatal(mgr.add(link_actors.task()))
