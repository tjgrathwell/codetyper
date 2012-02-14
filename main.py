#!/usr/bin/env python

import os
import pyglet
import random
import re
import sys
import time
from pyglet.window import mouse, key
from pyglet.gl import *

DEBUG = False

def drawQuad(x,y,w,h,hollow=False):
    # in screen space
    type = pyglet.gl.GL_LINE_LOOP if hollow else pyglet.gl.GL_QUADS
    pyglet.graphics.draw(4, type,('v2f', (x,     y,
                                          x + w, y,
                                          x + w, y - h,
                                          x,     y - h)))

class Screen(object):
    width, height = 1000, 480

class HighScores(object):
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
        return sorted(cls.scores, lambda x,y: y.points() - x.points())

class Colors(object):
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

class CodeSnippet(object):
    def __init__(self, code): # code is an array of lines
        self.code = self.clean(code)
        self.line = 0
        self.cursor = 0
        self.render()

    def clean(self, raw_code):
        cleanlines = [line.rstrip() + '\n' for line in raw_code.split('\n')]

        while cleanlines[0].strip() == '':
            cleanlines.pop(0)

        while cleanlines[-1].strip() == '':
            cleanlines.pop()

        return cleanlines

    def render(self):
        # We preserve any actual { } from the original text and escape them later on.
        # This is done so that we can boldenate the current character without
        #   having to worry about the case of {{ or }}
        b1, b2 = chr(254), chr(255)
        raw_code = [line.replace('{',b1).replace('}',b2) for line in self.code]

        raw_code_strings = None
        current_line = raw_code[self.line]

        # BUG : Lines that end in { stop showing the { when that's typed on. rstrip's fault?
        if self.cursor == len(self.code[self.line]) - 1:
            raw_code_strings = [
                current_line.rstrip(),
                ' {color %s}[RETURN]{color %s}\n' % (Colors.st('green'), Colors.st('white')),
            ]
        else:
            raw_code_strings = [
                current_line[:self.cursor],
                '{underline %s}{color %s}' % (Colors.st('red'), Colors.st('red')),
                current_line[self.cursor:self.cursor+1],
                '{color %s}{underline false}' % Colors.st('white'),
                current_line[self.cursor+1:]
            ]

        raw_code[self.line] = ''.join(raw_code_strings)

        escaped_code = ' '.join(raw_code).replace(b1,'{{').replace(b2,'}}')
        styled = "{font_name 'Consolas'}{font_size 10}{color %s} %s" % (
            Colors.st('gray'),
            escaped_code)

        document = pyglet.text.decode_attributed(styled)
        self.layout = pyglet.text.layout.TextLayout(
            document,
            multiline=True,
            width=Screen.width - 60,
            height=Screen.height)

    def type_on(self, char):
        if self.code[self.line][self.cursor] == char:
            self.cursor += 1
            self.render()
            return char
        return False

    def key_on(self, this_key):
        if this_key == key.TAB:
            [self.type_on(' ') for i in xrange(4)]

        if this_key == key.ENTER:
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

class FloatingText(object):
    negative = [
        "You suck!",
        "Stop typing wrong!",
        "Come on, now!",
        "Hey! Type better!",
        "Terrible!",
        "Awful!",
        "Shape up!",
        "Stop missing!",
        "Dude! Type correctly!"
    ]
    line = [
        "Keep going!",
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
        "Cool!"
    ]
    para = [
        "Way to Go!",
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
        "Dude!!"
    ]

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

        self.label = pyglet.text.Label(
            self.word,
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

class Stopwatch(object):
    def __init__(self,totaltime):
        self.totaltime = float(totaltime)
        self.started = False

    def go(self):
        self.started = time.time()

    def out(self):
        return (time.time() - self.started) > self.totaltime

    def draw(self):
        remaining = self.totaltime
        if self.started:
            remaining -= (time.time() - self.started)

        pyglet.text.Label(
            '%.2f' % remaining,
            color=Colors.t('green'),
            font_name='Consolas',
            font_size=32,
            x=Screen.width, y=Screen.height//2,
            anchor_y='center', anchor_x='right').draw()

class Score(object):
    LINE_AFFIRM_THRESHOLD = 40

    def __init__(self):
        self.success = 0
        self.misses = 0
        self.total = 0
        self.start_time = time.time()
        self.total_time = None
        self.FloatingText_queued = 0

    def key(self):
        self.total += 1

    def hit(self, this_key = None):
        self.success += 1
        # queue an FloatingText every somany characters
        if self.success % Score.LINE_AFFIRM_THRESHOLD == 0:
            self.FloatingText_queued = True
        if this_key and this_key == key.ENTER and self.FloatingText_queued:
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

    def elapsed_time(self):
        if self.total_time:
            return self.total_time
        return time.time() - self.start_time

    def get_cps(self):
        elapsed = self.elapsed_time()
        if not elapsed: return 0
        return '%.4f' % (self.success / elapsed)

    def finish(self, time_taken):
        self.total_time = time_taken

    def points(self):
        if not self.total_time:
            return 0

        return int(self.total_time * float(self.get_cps()))

    def high_score_text(self):
        if not self.total_time:
            return ''

        return 'name: %s, points: %s, cps: %s, misses: %s' % (
            'You!',
            self.points(),
            self.get_cps(),
            self.misses)

    def during_play_text(self):
        return 'fail percentage: %s\nmisses: %s\ncps: %s' % (
            self.miss_rate(),
            self.misses,
            self.get_cps())

    def draw(self):
        label = pyglet.text.Label(
            self.during_play_text(),
            color=Colors.t('green'),
            font_name='Consolas',
            font_size=10,
            x=Screen.width, y=0,
            anchor_y='bottom', anchor_x='right',
            multiline = True,
            width = Screen.width // 4,
            halign='center')
        label.draw()

class SnippetMonger(object):
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
    def all_snippets(cls):
        return cls.snippets.keys()

    @classmethod
    def set_preferred_snippets(cls, preferred):
        cls.preferred = preferred

    @classmethod
    def next(cls):
        snippet_group = cls.snippets[random.choice(cls.preferred)]
        snippet = random.choice(snippet_group)
        return CodeSnippet(snippet)

class GameScreen(object):
    def __init__(self):
        self.new_screen = False

    def key_press(self, this_key, modifiers):
        pass

    def key_type(self,text):
        pass

    def tick(self,dt):
        pass

class MainGameScreen(GameScreen):
    def __init__(self):
        super(MainGameScreen, self).__init__()
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

    def key_press(self,key,modifiers):
        hit, winner = self.current_snippet.key_on(key)
        if winner: # beat a snippet, show a strongly positive message
            self.new_word()
            self.show_message('snippet')
        elif hit:
            should_show_message = self.scorer.hit(key)
            if should_show_message: # did a line, show a weakly positive message
                self.show_message('line')

    def key_type(self, char):
        if ord(char) == 13: # newline
            return

        if char.strip():
            self.scorer.key()

        char_hit = self.current_snippet.type_on(char)
        if char_hit:
            if char_hit.strip(): # don't score hits for whitespace
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
            self.scorer.finish(self.stopwatch.totaltime)
            HighScores.add(self.scorer)
            self.new_screen = RoundOverScreen(self.scorer)

    def draw(self):
        self.current_snippet.draw()
        self.scorer.draw()
        self.stopwatch.draw()
        for message in self.messages:
            message.draw()

class Option(object):
    def __init__(self,name,color=Colors.t('white'),x=0,y=0,has_checkbox=False,checked=False):
        self.name = name
        self.color = color
        self.x, self.y = x,y
        self.has_checkbox = has_checkbox
        self.checked = checked
        self.label = pyglet.text.Label(
            name,
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
        if self.has_checkbox:
            if self.checked:
                drawQuad(self.x-self.label.content_width//2 - 20, self.y+5, 10, 10)
            else:
                drawQuad(self.x-self.label.content_width//2 - 20, self.y+5, 10, 10, hollow=True)

class Options(object):
    def __init__(self, option_names, x, y, checked_options = None):
        self.options = []
        for name in option_names:
            if (checked_options is not None):
                is_checked = (name in checked_options)
                self.options.append(Option(name, has_checkbox=True, checked=is_checked))
            else:
                self.options.append(Option(name, has_checkbox=False, checked=True))

        self.select(0)
        self.x, self.y = x,y
        self.has_checkboxes = (checked_options is not None)
        self.arrange()

    def arrange(self):
        self.options[0].x, self.options[0].y = self.x, self.y
        y = self.y
        for option in self.options:
            option.move(self.x,y)
            y -= option.label.content_height

    def select(self,n):
        self.selected = n
        for option in self.options[:self.selected] + self.options[self.selected+1:]:
            option.set_color(Colors.t('white'))
        self.options[self.selected].set_color(Colors.t('red'))

    def value(self):
        return self.options[self.selected].name

    def get_checked(self):
        if self.has_checkboxes:
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
        super(HighScoresScreen, self).__init__()
        self.label = pyglet.text.Label(
            'everyone is a winner',
            color=Colors.t('white'),
            font_name='Arial',
            font_size=32,
            x=Screen.width//2, y=Screen.height*.9,
            anchor_y='center', anchor_x='center')

        self.scorelabels = []
        for score in HighScores.get_sorted():
            newlabel = pyglet.text.Label(
                score.high_score_text(),
                color=Colors.t('white'),
                font_name='Arial',
                font_size=16,
                x=Screen.width//2, y=y,
                anchor_y='center', anchor_x='center')

            self.scorelabels.append(newlabel)
            y -= newlabel.content_height

    def key_press(self, this_key, modifiers):
        if this_key == key.ENTER or this_key == key.BACKSPACE:
            self.new_screen = SplashScreen()

    def draw(self):
        self.label.draw()
        [score.draw() for score in self.scorelabels]

class RoundOverScreen(GameScreen):
    def __init__(self,score):
        super(RoundOverScreen, self).__init__()

        self.label = pyglet.text.Label(
            'i think you did alright',
            color=Colors.t('white'),
            font_name='Arial',
            font_size=32,
            x=Screen.width//2, y=Screen.height*.9,
            anchor_y='center', anchor_x='center')

        self.scorelabel = pyglet.text.Label(
            score.high_score_text(),
            color=Colors.t('white'),
            font_name='Arial',
            font_size=16,
            x=Screen.width//2, y=Screen.height//2,
            anchor_y='center', anchor_x='center')

    def key_press(self, this_key, modifiers):
        if this_key == key.ENTER or this_key == key.BACKSPACE:
            self.new_screen = HighScoresScreen()

    def draw(self):
        self.label.draw()
        self.scorelabel.draw()

class OptionsScreen(GameScreen):
    def __init__(self):
        super(OptionsScreen, self).__init__()

        self.label = pyglet.text.Label(
            'space toggles a snippetset, enter or backspace goes back',
            color=Colors.t('white'),
            font_name='Arial',
            font_size=16,
            x=Screen.width//2, y=Screen.height//2,
            anchor_y='center', anchor_x='center')

        self.options = Options(
            SnippetMonger.all_snippets(),
            checked_options = SnippetMonger.preferred,
            x = Screen.width//2, y = Screen.height//3.5)

    def key_press(self, this_key, modifiers):
        if this_key == key.SPACE:
            self.options.toggle()
        if this_key == key.BACKSPACE or this_key == key.ENTER:
            SnippetMonger.set_preferred_snippets(self.options.get_checked())
            self.new_screen = SplashScreen()
        elif this_key == key.UP:
            self.options.up()
        elif this_key == key.DOWN:
            self.options.down()

    def draw(self):
        self.label.draw()
        self.options.draw()

class SplashScreen(GameScreen):
    subtitles = [
        "Hyper Fighting Edition",
        "Alpha Turbo",
        "After Dark",
        "Electric Boogaloo",
        "Zeta Prime",
        "Professional",
        "Deluxe Edition",
        "Vista",
        "MMVIII"
    ]

    def __init__(self):
        super(SplashScreen, self).__init__()

        self.label = pyglet.text.Label(
            'CODE TYPER',
            color=Colors.t('white'),
            font_name='Arial',
            font_size=64,
            x=Screen.width//10, y=Screen.height*.9,
            anchor_y='top', anchor_x='left')

        self.sublabel = pyglet.text.Label(
            random.choice(SplashScreen.subtitles),
            color=Colors.t('gray'),
            font_name='Arial',
            font_size=16,
            x = self.label.x + self.label.content_width*.8,
            y = self.label.y - self.label.content_height,
            anchor_y='top', anchor_x='center')

        self.options = Options(
            ['Start', 'Options', 'High Scores', 'Exit'],
            x=Screen.width//2, y=Screen.height//3.5)

        self.drawables = [self.label, self.sublabel, self.options]

    def key_press(self, this_key, modifiers):
        if this_key == key.ENTER or this_key == key.SPACE:
            if self.options.value()=='Start':
                self.new_screen = MainGameScreen()
            elif self.options.value()=='High Scores':
                self.new_screen = HighScoresScreen()
            elif self.options.value()=='Options':
                self.new_screen = OptionsScreen()
            elif self.options.value()=='Exit':
                sys.exit()
        elif this_key == key.UP:
            self.options.up()
        elif this_key == key.DOWN:
            self.options.down()

    def draw(self):
        [obj.draw() for obj in self.drawables]

class GameState(object):
    def __init__(self):
        self.current_screen = SplashScreen()

    def check_screen(self):
        if self.current_screen.new_screen:
            self.current_screen = self.current_screen.new_screen

    def key_press(self, this_key, modifiers):
        self.current_screen.key_press(this_key, modifiers)
        self.check_screen()

    def key_type(self, char):
        self.current_screen.key_type(char)
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
def on_key_press(this_key, modifiers):
    G.state.key_press(this_key, modifiers)

@G.window.event
def on_text(text):
    G.state.key_type(text)

# http://stackoverflow.com/questions/1714027/version-number-comparison
def cmpversion(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return cmp(normalize(version1), normalize(version2))

if __name__ == '__main__':
    if cmpversion(pyglet.version, '1.1') < 0:
        print 'you need pyglet 1.1 or greater'
        sys.exit()

    pyglet.gl.glClearColor(*Colors.black)

    SnippetMonger.load()

    G.window.set_icon(pyglet.image.load(os.path.join('.', 'codetyper.ico')))

    # not sure why it doesn't animate smoothly at 60,
    #   do I have to do interpolation in draw() or what...?
    pyglet.clock.schedule_interval(G.state.tick, 1/120.0)

    pyglet.app.run()
