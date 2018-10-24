import sys, time, socket, urllib2, json
from bs4 import BeautifulSoup
 
class ircProtocol:
    def __init__(self):#Configuration
        self.host = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nick = 'OblivBot'
        self.chan = '#uhhobliv'
        self.oauth = '#oauth'
        self.header = {
            'Origin': None,
            'Accept-Charset': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Riot-Token': 'riot-token',
            'Accept-Language': 'en-US,en;q=0.5',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        self.summoner = None
        self.accountId = None
        self.content = None
        self.items = None
        self.inGameList = []
        self.commandList = {
            '!cg':'Current game player list with ranks',
            '!schedule':'Schedule for streaming',
            '!getbuild <champion>':'Get best build for a champion selected'
                           }
       
    def connect(self):#Connect to IRC Socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        self.s.send('PASS %s \r\n' % self.oauth)
        self.s.send('NICK %s\r\n' % self.nick)
        self.s.send('CAP REQ :twitch.tv/commands \r\n')
        self.s.send('CAP REQ :twitch.tv/membership \r\n')
                   
    def recv(self):#Read recieved Packets
        try:
            self.data = self.s.recv(2048)
            self.data = self.data.decode('utf-8')
            self.s.settimeout(10)
            print self.data
            return self.data
        except Exception as e:
            print e
            self.s.close()
            quit()
   
    def pong(self):#Stay connected
        if 'PING :tmi.twitch.tv' in self.data:
            self.s.send('PONG :tmi.twitch.tv \r\n')
        else:
            pass
   
    def joinChan(self):#Join Channel
        if ':You are in a maze of twisty passages, all alike.' in self.data:
            self.s.send('JOIN %s \r\n' % self.chan)
        else:
            pass
   
    def requestUrl(self, url):
        try:
            r = urllib2.Request(url, headers=self.header)
            self.content = urllib2.urlopen(r)
        except Exception as e:
            pass
   
    def getSummonerName(self, summonerId):
        self.requestUrl('https://na1.api.riotgames.com/lol/summoner/v3/summoners/' + summonerId)
        summoner = json.load(self.content)
        self.summoner = summoner['name']
   
    def getRank(self, summonerId):#need to check for unranked aswell
        self.requestUrl('https://na1.api.riotgames.com/lol/league/v3/leagues/by-summoner/' + summonerId)
        players = json.load(self.content)
        p = players[0]['entries']
        self.getSummonerName(summonerId)
        for i in p:
            if self.summoner in i['playerOrTeamName']:
                self.inGameList.append(i['playerOrTeamName'] + ' ' + players[0]['tier'] + ' ' + i['rank'])
            else:
                pass
   
    def getAccId(self, summoner):
        self.requestUrl('https://na1.api.riotgames.com/lol/summoner/v3/summoners/by-name/' + summoner)
        information = json.load(self.content)
        print information['accountId']
        self.accountId = information['accountId']

    def getBuild(self, champion):
        self.requestUrl('http://www.probuilds.net/champions/details/' + champion)
        soup = BeautifulSoup(self.content, 'html.parser')
        divs = soup.find_all('div', {'class':'final-builds popular-items'})
        items = []
        for i in divs:
            lines = i.text.split('\n')
            items.append([x for x in lines if x != '' and not x.isdigit()])
        self.items = items[0][6:12]
        print self.items
        for i in self.items:
            print i
            #if float(i.rstrip('%')).isdigit():
            #    pass
            #else:
            #    self.s.send('PRIVMSG %s :Top 3 items &#58 %s \r\n' % (self.chan, i))
       
    def getGameStats(self, summonerId):
        self.requestUrl('https://na1.api.riotgames.com/lol/spectator/v3/active-games/by-summoner/' + summonerId)
        try:
            playerList = json.load(self.content)
            for i in playerList['participants']:
                self.getRank(str(i['summonerId']))
                self.s.send('PRIVMSG %s :%s \r\n' % (self.chan, ', '.join(self.inGameList)))
                self.inGameList = []
        except Exception as e:
            self.s.send('PRIVMSG %s :%s \r\n' % (self.chan, 'Currently not in game!'))
 
    def commandHandler(self):#not finished
        try:
            parameter = self.data.split(':')[2].split(' ', 1)[1]
        except:
            pass
        if '!test' in self.data:
            self.s.send('PRIVMSG %s :Bot test 123 \r\n' % (self.chan))
        if '!cg' in self.data:
            try:
                self.getAccId(parameter.strip().replace(' ', '%'))
                self.getGameStats(self.accountId)
            except Exception as e:
                print e
        if '!schedule' in self.data:
            self.s.send('PRIVMSG %s :Monday 8 am to 12 pm (gaming or programming)\r\n' % (self.chan))
            self.s.send('PRIVMSG %s :Tuesday: 8 am to 12 pm (programming)\r\n' % (self.chan))
            self.s.send('PRIVMSG %s :Thursday: 8 am to 12 pm (gaming or programming)\r\n' % (self.chan))
            self.s.send('PRIVMSG %s :Friday: 6 pm to 10 pm (gaming)\r\n' % (self.chan))
            self.s.send('PRIVMSG %s :Saturday: 12 pm to 3 pm (programming)\r\n' % (self.chan))
        if '!commandlist' in self.data:
            for command, explan in self.commandList.items():
                self.s.send('PRIVMSG %s :%s - %s\r\n' % (self.chan, command, explan))
        if '!getbuild' in self.data:
            try:
                self.getBuild(parameter.strip())
            except Exception as e:
                print e


#Run bot function
if __name__ == '__main__':
    ircBot = ircProtocol()
    ircBot.connect()
   
    while True:
        ircBot.recv()
        ircBot.joinChan()
        ircBot.pong()
        ircBot.commandHandler()