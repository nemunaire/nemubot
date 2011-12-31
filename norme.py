import re
import os
import subprocess

def launch(s, sender, msgpart):
        result = re.match(".*((dans|in) (la |the )?bran?ch?e?|(dans|in) (la |the )?bran?c?he?) +([^ ]+).*", msgpart)
        if result is not None:
            branch = "acu/" + result.group(6);
        else:
            branch = "master"

        result = re.match(".*(dans|in) (la |the |le fichier |le dossier )?([^b][^r][^ ]+).*", msgpart)
        if result is not None and re.search("(^/|.*\.\..*)", result.group(3)) is None:
            checkpath = result.group(3)
            if not os.path.exists(checkpath):
                if os.path.exists("./src/" + checkpath):
                    checkpath = "./src/" + checkpath
                else:
                    dirList = os.listdir("./src/")
                    for f in dirList:
                        if os.path.exists("./src/" + os.path.basename(f) + "/" + checkpath):
                            checkpath = "./src/" + os.path.basename(f) + "/" + checkpath
                            break

                    if not os.path.exists(checkpath):
                        s.send("PRIVMSG %s :I don't find %s in branch %s\r\n" % (sender[0], checkpath, branch))
                        return
        else:
            checkpath = "./src/"

        if subprocess.call(["git", "checkout", branch]) == 0:
            try:
                #s.send("PRIVMSG %s :Let me check %s in %s\r\n" % (sender[0], branch, checkpath))
                faults = subprocess.check_output(["/home/nemunaire/workspace_/moulinette/main.py", checkpath])
                lines = faults.split('\n')
                for l in lines:
                    if len(l) > 1:
                        #print l
                        #print sender
                        s.send("PRIVMSG %s :%s\r\n" % (sender[0], l))
            except:
                s.send("PRIVMSG %s :An error occurs, all is broken\r\n" % sender[0])
        else:
            s.send("PRIVMSG %s :I haven't the branch %s here.\r\n" % (sender[0], branch))
