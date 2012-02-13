#!/usr/bin/env python

import pyglet
from pyglet.window import mouse
from pyglet.window import key
from pyglet.gl import *
import random
import time
import os
import sys

DEBUG = False

def drawQuad(x,y,w,h,hollow=False):
    # in screen space
    type = pyglet.gl.GL_LINE_LOOP if hollow else pyglet.gl.GL_QUADS
    pyglet.graphics.draw(4, type,('v2f', (x,     y,
                                          x + w, y,
                                          x + w, y - h,
                                          x,     y - h)))

class Screen:
    width, height = 1000, 480

class HighScores:
    scores = []

    @classmethod
    def load(cls,file):
        pass

    @classmethod
    def save(cls,file):
        pass

    @classmethod
    def add(cls,score):
        cls.scores.append(score)

    @classmethod
    def get_sorted(cls):
        return sorted(cls.scores, lambda x,y: y['points'] - x['points'])

class Colors:
    white  = 1, 1, 1, 1
    green  = 0, 1, 0, 1
    black  = 0, 0, 0, 1
    gray   = .7, .7, .7, 1
    red    = 1, 0, 0, 1
    blue   = .2, .2, .8, 1
    yellow = .8, .2, .8, 1
    red2   = .8, .2, .2, 1

    @classmethod
    def t(cls, name):
        # get a tuple of a color multiplied up to 0-255
        if hasattr(Colors, name):
            col = getattr(Colors, name)
        else:
            col = Colors.white
        return [int(v * 255) for v in col]

    @classmethod
    def st(cls, name):
        # get a tuple of a color multiplied up to 0-255, as a string
        return str(Colors.t(name))

class CodeSnippet:
    def __init__(self, code, clean=False): # code is an array of lines
        self.code = code if not clean else self.clean(code)
        self.line, self.cursor = 0, 0
        self.render()

    def clean(self, raw_code):
        cleanlines = [line.rstrip() + '\n' for line in raw_code.split('\n')]
        while not cleanlines[0].strip():
            cleanlines.pop(0)
        while not cleanlines[-1].strip():
            cleanlines.pop()
        return cleanlines

    def render(self):
        # We preserve any actual { } from the original text and escape them later on.
        # This is done so that we can boldenate the current character without
        #   having to worry about the case of {{ or }}
        b1, b2 = chr(254), chr(255)
        temp_code = [line.replace('{',b1).replace('}',b2) for line in self.code]
        # BUG : Lines that end in { stop showing the { when that's typed on. rstrip's fault?
        if self.cursor == len(self.code[self.line]) - 1:
            temp_code[self.line] = ''.join([temp_code[self.line].rstrip(),
                                            ' {color %s}[RETURN]{color %s}\n' % (Colors.st('green'), Colors.st('white'))])
        else:
            temp_code[self.line] = ''.join([temp_code[self.line][:self.cursor],
                                       '{underline %s}{color %s}' % (Colors.st('red'), Colors.st('red')),
                                       temp_code[self.line][self.cursor:self.cursor+1],
                                       '{color %s}{underline false}' % Colors.st('white'),
                                       temp_code[self.line][self.cursor+1:]])
        if DEBUG:
            print temp_code[self.line]
        escaped_code = ' '.join(temp_code).replace(b1,'{{').replace(b2,'}}')
        styled = "{font_name 'Consolas'}{font_size 10}{color %s} %s" % (Colors.st('gray'), escaped_code)

        document = pyglet.text.decode_attributed(styled)
        self.layout = pyglet.text.layout.TextLayout(document, multiline=True, width=Screen.width - 60, height=Screen.height)

    def type_on(self, text):
        if self.code[self.line][self.cursor] == text:
            self.cursor += 1
            self.render()
            return text
        return False

    def symbol_on(self, symbol):
        if symbol == key.TAB:
            [self.type_on(' ') for i in xrange(4)]
        if symbol == key.ENTER:
            if self.cursor == len(self.code[self.line]) - 1:
                self.cursor = 0
                self.line += 1
                if self.line == len(self.code):
                    return True, True
                self.render()
            return True, False
        return False, False

    def draw(self):
        self.layout.draw()

class FloatingText:
    negative = ["You suck!",
                "Stop typing wrong!",
                "Come on, now!",
                "Hey! Type better!",
                "Terrible!",
                "Awful!",
                "Shape up!",
                "Stop missing!",
                "Dude! Type correctly!"]
    line     = ["Keep going!",
                "You can do it!",
                "We're counting on you!",
                "Good one!",
                "Nice line!",
                "Nice one!",
                "Alright!",
                "Keep it together!",
                "You're doing great!",
                "Great job!",
                "Keep typing!",
                "Cool!"]
    para     = ["Way to Go!",
                "You're the Best!",
                "Awesome!",
                "Spectacular!",
                "You win at life!",
                "Success!",
                "How great for you!",
                "We're all so proud!",
                "Tubular!",
                "Amazing!",
                "Smashing!",
                "Fabulous!",
                "Fantastic!",
                "Unbelievable!",
                "Tremendous!",
                "Incredible!",
                "Delightful!",
                "Hooray!",
                "OMG!!!",
                "Dude!!"]

    def __init__(self,type='line'):
        if type == 'line':
            self.color = Colors.t('yellow')
            self.word = random.choice(FloatingText.line)
        elif type == 'snippet':
            self.color = Colors.t('blue')
            self.word = random.choice(FloatingText.para)
        elif type == 'negative':
            self.color = Colors.t('red2')
            self.word = random.choice(FloatingText.negative)
        else:
            raise Exception
        self.label = pyglet.text.Label(self.word, 
                       color=self.color,
                       bold=True,
                       font_name='Arial', 
                       font_size=64,
                       anchor_y='center', anchor_x='center')
        # choose a random offscreen point by picking an x then a y
        self.startx = random.uniform(-Screen.width//2, Screen.width*(3/2))
        if random.choice([0,1]):
            self.starty = -Screen.height//2
        else:
            self.starty = Screen.height*(3/2)
        self.targetx, self.targety = Screen.width//2, Screen.height//2
        self.label.x, self.label.y = self.startx, self.targetx
        self.elapsed = 0
        self.total_time = random.uniform(1,2)

    def tick(self,dt):
        self.elapsed += dt
        
        if abs(self.total_time - self.elapsed) > 2:
            return False
        
        # make a value from 0 to total time where 0 is closest to the center
        far_awayness = min(abs(self.total_time - self.elapsed), self.total_time) * 1/self.total_time
        opc = min((1-far_awayness) * 1.6, 1.0) # 1.6 is magic value chosen by my mind
        self.color[3] = int(opc * 255) # set opacity
        self.label.color = self.color
        
        proportion = self.elapsed / self.total_time
        self.label.x = self.startx + (self.targetx-self.startx) * proportion
        self.label.y = self.starty + (self.targety-self.starty) * proportion
        
        return True

    def draw(self):
        self.label.draw()

class Stopwatch:
    def __init__(self,totaltime):
        self.totaltime = totaltime
        self.started = False

    def go(self):
        self.started = time.time()

    def out(self):
        return (time.time() - self.started) > self.totaltime

    def draw(self):
        remaining = self.totaltime - (time.time() - self.started) if self.started else self.totaltime
        pyglet.text.Label('%.2f' % remaining, 
                       color=Colors.t('green'),
                       font_name='Consolas', 
                       font_size=32,
                       x=Screen.width, y=Screen.height//2,
                       anchor_y='center', anchor_x='right').draw()

class Score:
    LINE_AFFIRM_THRESHOLD = 40

    def __init__(self):
        self.success = 0
        self.misses = 0
        self.total = 0
        self.start_time = time.time()
        self.FloatingText_queued = 0

    def key(self):
        self.total += 1

    def hit(self,symbol=None):
        self.success += 1
        # queue an FloatingText every somany characters
        if self.success % Score.LINE_AFFIRM_THRESHOLD == 0:
            self.FloatingText_queued = True
        if symbol and symbol == key.ENTER and self.FloatingText_queued:
            self.FloatingText_queued = False
            return True

    def miss(self):
        self.misses += 1
        if self.misses % 10 == 0:
            return True
        return False

    def success_rate(self):
        if not self.total: return 0
        return '%.4f' % (self.success / float(self.total))

    def miss_rate(self):
        if not self.total: return 0
        return '%.4f' % (self.misses / float(self.total))

    def get_cps(self):
        elapsed = time.time() - self.start_time
        if not elapsed: return 0
        return '%.4f' % (self.success / elapsed)

    def get_result(self,time_taken):
         return {
             'name' : 'You!',
             'cps' : self.get_cps(),
             'misses' : self.misses,
             'points' : int(time_taken*float(self.get_cps()))}

    def draw(self):
        scoretext = 'fail percentage: %s\nmisses: %s\ncps: %s' % (self.miss_rate(), self.misses, self.get_cps())
        pyglet.text.Label(
            scoretext, 
            color=Colors.t('green'),
            font_name='Consolas', 
            font_size=10,
            x=Screen.width, y=0,
            anchor_y='bottom', anchor_x='right',
            multiline = True,
            width = Screen.width // 4,
            halign='center').draw()

class SnippetMonger:
    @classmethod
    def load(cls):
        snippets_dir = os.path.join('.', 'snippets')
        cls.snipfiles = [file for file in os.listdir(snippets_dir) if file.endswith('snp')]
        cls.snippets = {}
        for file in cls.snipfiles:
            long_filename = os.path.join(snippets_dir, file)
            snippets = open(long_filename).read().split('|||||=====|||||')
            cls.snippets[file] = filter(lambda snp: len(snp), snippets)
        cls.preferred = cls.snippets.keys()

    @classmethod
    def get_languages(cls):
        return cls.snippets.keys()

    @classmethod
    def set_preferred_languages(cls,preferred):
        cls.preferred = preferred

    @classmethod
    def next(cls):
        snippet_group = cls.snippets[random.choice(cls.preferred)]
        snippet = random.choice(snippet_group)
        return CodeSnippet(snippet, clean=True)

class GameScreen:
    def __init__(self):
        self.new_screen = False

    def key_press(self,symbol,modifiers):
        pass

    def key_type(self,text):
        pass

    def tick(self,dt):
        pass

class MainGameScreen(GameScreen):
    def __init__(self):
        GameScreen.__init__(self)
        self.reset()
        self.messages = []

    def reset(self):
        self.scorer = Score()
        self.stopwatch = Stopwatch(120)
        self.stopwatch.go()
        self.new_word()

    def new_word(self):
        self.current_snippet = SnippetMonger.next()

    def show_message(self,type='line'):
        self.messages.append(FloatingText(type))

    def key_press(self,symbol,modifiers):  
        hit, winner = self.current_snippet.symbol_on(symbol)
        if winner: # beat a snippet, show a strongly positive message
            self.new_word()
            self.show_message('snippet')
        elif hit:
            affirm = self.scorer.hit(symbol)
            if affirm: # did a line, show a weakly positive message
                self.show_message('line')

    def key_type(self,text):
        if ord(text) == 13: # probably platform specific newline hack
            return
        if text.strip():
            self.scorer.key()
        text_hit = self.current_snippet.type_on(text)
        if text_hit:
            if text_hit.strip(): # don't score hits for whitespace
                self.scorer.hit()
        else:
            neg = self.scorer.miss()
            if neg:
                self.show_message('negative')

    def tick(self,dt):
        dead = []
        for message in self.messages:
            alive = message.tick(dt)
            if not alive: dead.append(message)
        [self.messages.remove(message) for message in dead]
        if self.stopwatch.out():
            result = self.scorer.get_result(self.stopwatch.totaltime)
            HighScores.add(result)
            self.new_screen = RoundOverScreen(result)

    def draw(self):
        self.current_snippet.draw()
        self.scorer.draw()
        self.stopwatch.draw()
        for message in self.messages:
            message.draw()

class Option:
    def __init__(self,name,color=Colors.t('white'),x=0,y=0,checkbox=False,checked=False):
        self.name = name
        self.color = color
        self.x, self.y = x,y
        self.checkbox = checkbox
        self.checked = checked
        self.label = pyglet.text.Label(name, 
                       color=self.color,
                       font_name='Arial', 
                       font_size=16,
                       x=self.x, y=self.y,
                       anchor_y='center', anchor_x='center')

    def set_color(self,color):
        self.label.color = color

    def move(self,x,y):
        self.x,self.y = x,y

    def draw(self):
        self.label.x, self.label.y = self.x, self.y
        self.label.draw()
        if self.checkbox:
            if self.checked:
                drawQuad(self.x-self.label.content_width//2 - 20, self.y+5, 10, 10)
            else:
                drawQuad(self.x-self.label.content_width//2 - 20, self.y+5, 10, 10, hollow=True)

class Options:
    def __init__(self,option_names,x,y,checkbox=False):
        self.options = [Option(name,checkbox=checkbox,checked=True) for name in option_names]
        self.select(0)
        self.x, self.y = x,y
        self.checkbox = checkbox
        self.arrange()

    def arrange(self):
        self.options[0].x, self.options[0].y = self.x, self.y
        y = self.y
        for option in self.options:
            option.move(self.x,y)
            y -= option.label.content_height

    def select(self,n):
        self.selected = n
        for option in self.options[:self.selected]+self.options[self.selected+1:]:
            option.set_color(Colors.t('white'))
        self.options[self.selected].set_color(Colors.t('red'))

    def value(self):
        return self.options[self.selected].name

    def get_checked(self):
        if self.checkbox:
            return [option.name for option in self.options if option.checked]
        else:
            return []

    def toggle(self):
        self.options[self.selected].checked = not self.options[self.selected].checked

    def up(self):
        if self.selected > 0:
            self.select(self.selected-1)

    def down(self):
        if self.selected < len(self.options)-1:
            self.select(self.selected+1)

    def draw(self):
        for option in self.options:
            option.draw()

class HighScoresScreen(GameScreen):
    def __init__(self,y=Screen.height*.8):
        GameScreen.__init__(self)
        self.label = pyglet.text.Label('everyone is a winner', 
                       color=Colors.t('white'),
                       font_name='Arial', 
                       font_size=32,
                       x=Screen.width//2, y=Screen.height*.9,
                       anchor_y='center', anchor_x='center')
        self.scorelabels = []
        for score in HighScores.get_sorted():
            textual = 'name: %s, points: %s, cps: %s, misses: %s' % (score['name'], score['points'], score['cps'], score['misses'])
            newlabel = pyglet.text.Label(textual, 
                           color=Colors.t('white'),
                           font_name='Arial', 
                           font_size=16,
                           x=Screen.width//2, y=y,
                           anchor_y='center', anchor_x='center')
            self.scorelabels.append(newlabel)
            y -= newlabel.content_height

    def key_press(self,symbol,modifiers):
        if symbol == key.ENTER or symbol == key.BACKSPACE:
            self.new_screen = Splash()

    def draw(self):
        self.label.draw()
        [score.draw() for score in self.scorelabels]

class RoundOverScreen(GameScreen):
    def __init__(self,score):
        GameScreen.__init__(self)
        self.label = pyglet.text.Label('i think you did alright', 
                       color=Colors.t('white'),
                       font_name='Arial', 
                       font_size=32,
                       x=Screen.width//2, y=Screen.height*.9,
                       anchor_y='center', anchor_x='center')
        textual = 'name: %s, points: %s, cps: %s, misses: %s' % (score['name'], score['points'], score['cps'], score['misses'])
        self.scorelabel = pyglet.text.Label(textual, 
                       color=Colors.t('white'),
                       font_name='Arial', 
                       font_size=16,
                       x=Screen.width//2, y=Screen.height//2,
                       anchor_y='center', anchor_x='center')

    def key_press(self,symbol,modifiers):
        if symbol == key.ENTER or symbol == key.BACKSPACE:
            self.new_screen = HighScoresScreen()

    def draw(self):
        self.label.draw()
        self.scorelabel.draw()

class OptionsScreen(GameScreen):
    def __init__(self):
        GameScreen.__init__(self)
        self.label = pyglet.text.Label('space toggles a snippetset, backspace goes back', 
                       color=Colors.t('white'),
                       font_name='Arial', 
                       font_size=16,
                       x=Screen.width//2, y=Screen.height//2,
                       anchor_y='center', anchor_x='center')
        self.options = Options(SnippetMonger.get_languages(),
                               x=Screen.width//2, y=Screen.height//3.5,
                               checkbox=True)

    def key_press(self,symbol,modifiers):
        if symbol == key.SPACE or symbol == key.ENTER:
            self.options.toggle()
        if symbol == key.BACKSPACE:
            SnippetMonger.set_preferred_languages(self.options.get_checked())
            self.new_screen = Splash()
        elif symbol == key.UP:
            self.options.up()
        elif symbol == key.DOWN:
            self.options.down()

    def draw(self):
        self.label.draw()
        self.options.draw()

class Splash(GameScreen):
    subtitles = ["Hyper Fighting Edition",
                 "Alpha Turbo",
                 "After Dark",
                 "Electric Boogaloo",
                 "Zeta Prime",
                 "Professional",
                 "Deluxe Edition",
                 "Vista",
                 "MMVIII"]

    def __init__(self):
        GameScreen.__init__(self)
        self.label = pyglet.text.Label('CODE TYPER', 
                       color=Colors.t('white'),
                       font_name='Arial', 
                       font_size=64,
                       x=Screen.width//10, y=Screen.height*.9,
                       anchor_y='top', anchor_x='left')
        self.sublabel = pyglet.text.Label(random.choice(Splash.subtitles), 
                       color=Colors.t('gray'),
                       font_name='Arial', 
                       font_size=16,
                       x=self.label.x+self.label.content_width*.8, y=self.label.y-self.label.content_height,
                       anchor_y='top', anchor_x='center')
        self.options = Options(['Start', 'Options', 'High Scores', 'Exit'],
                                x=Screen.width//2, y=Screen.height//3.5)

    def key_press(self,symbol,modifiers):
        if symbol == key.ENTER or symbol == key.SPACE:
            if self.options.value()=='Start':
                self.new_screen = MainGameScreen()
            elif self.options.value()=='High Scores':
                self.new_screen = HighScoresScreen()
            elif self.options.value()=='Options':
                self.new_screen = OptionsScreen()
            elif self.options.value()=='Exit':
                sys.exit()
        elif symbol == key.UP:
            self.options.up()
        elif symbol == key.DOWN:
            self.options.down()

    def draw(self):
        self.label.draw()
        self.sublabel.draw()
        self.options.draw()
        
class GameState:
    def __init__(self):
        self.current_screen = Splash()

    def check_screen(self):
        if self.current_screen.new_screen:
            self.current_screen = self.current_screen.new_screen

    def key_press(self,symbol,modifiers):
        self.current_screen.key_press(symbol,modifiers)
        self.check_screen()

    def key_type(self,text):
        self.current_screen.key_type(text)
        self.check_screen()

    def tick(self,dt):
        self.current_screen.tick(dt)
        self.check_screen()

    def draw(self):
        self.current_screen.draw()

class G:
    window = pyglet.window.Window(
        caption = "code typer",
        width = Screen.width,
        height = Screen.height,
        resizable = True)
    state = GameState()
    fps_display = pyglet.clock.ClockDisplay() if DEBUG else None

@G.window.event
def on_draw():
    G.window.clear()
    G.state.draw()
    if G.fps_display: G.fps_display.draw()

@G.window.event
def on_key_press(symbol, modifiers):
    G.state.key_press(symbol, modifiers)

@G.window.event
def on_text(text):
    G.state.key_type(text)

if __name__ == '__main__':
    if '1.1' not in pyglet.version:
        print 'you need pyglet 1.1 beta 2 or greater'
        sys.exit()

    pyglet.gl.glClearColor(*Colors.black)

    SnippetMonger.load()

    # doesn't work well with OSX, unless  you can get pyglet to play nice
    #G.window.set_icon(pyglet.image.load(os.path.join('.', 'codetypericon.png')))

    # this is being stupid. it should animate smoothly at 60, do I have to do interpolation
    #   in draw() or what...?
    pyglet.clock.schedule_interval(G.state.tick, 1/120.0)

    pyglet.app.run()
