import inspect, discord, shutil, os, fake_useragent
import discord.http
def patched():
    try:
        return open("patched","r").read() == "true"
    except: return False

def patch():
    global discord
    if not patched():
        file = inspect.getabsfile(discord.HTTPClient)
        shutil.copyfile(file, "pypatchbck/"+os.path.basename(file))
        content = (open(file,"r").read()
                   .replace("""self.user_agent: str = user_agent.format(
            __version__, sys.version_info, aiohttp.__version__
        )""", "self.user_agent: str = '{0}'".format(fake_useragent.FakeUserAgent().random))
        .replace(r'f"Bot {self.token}"',"self.token"))
        open(file,"w").write(content)
        open("patched","w").write("true")
        print("alr patched")
        del discord