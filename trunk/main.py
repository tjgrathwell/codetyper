import pyglet
from pyglet.window import mouse
from pyglet.window import key
from pyglet.gl import *
import random
import time
import os

DEBUG = False

class Screen:
    width, height = 1000, 480

class Colors:
    white = 1, 1, 1, 1
    green = 0, 1, 0, 1
    black = 0, 0, 0, 1
    gray  = .7, .7, .7, 1
    red   = 1, 0, 0, 1
    blue  = .2, .2, .8, 1
    yellow = .8, .2, .8, 1
    red2  = .8, .2, .2, 1
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
        # Okay, so this is a hack: we preserve any actual { } from the original text and escape them later on.
        # This is done so that we can boldenate the current character without having to worry about the
        # case of {{ or }}
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
            return True
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

class Affirmation:
    line     = ["Keep going!",
                "You can do it!",
                "We're counting on you!",
                "Good one!",
                "Nice line!",
                "Nice one!",
                "Alright!",
                "Keep it together!",
                "You're doing great!"
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
    def __init__(self,strong=False):
        self.word = random.choice(Affirmation.para) if strong else random.choice(Affirmation.line)
        self.color = Colors.t('blue') if strong else Colors.t('yellow')
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
        
        # this whole bit is pretty bullshit. REFACTOR
        # make a value from 0 to total time where 0 is closest to the center
        far_awayness = min(abs(self.total_time - self.elapsed), self.total_time) * 1/self.total_time
        if far_awayness > 2:
            return False
        opc = min((1-far_awayness) * 1.6, 1.0) # 1.6 is magic value chosen by my mind
        self.color[3] = int(opc * 255) # set opacity
        self.label.color = self.color
        
        proportion = self.elapsed / self.total_time
        self.label.x = self.startx + (self.targetx-self.startx) * proportion
        self.label.y = self.starty + (self.targety-self.starty) * proportion
        
        return True
    def draw(self):
        self.label.draw()

class Score:
    LINE_AFFIRM_THRESHOLD = 40
    def __init__(self):
        self.success = 0
        self.misses = 0
        self.total = 0
        self.start_time = time.time()
        self.affirmation_queued = 0
    def key(self):
        self.total += 1
    def hit(self,symbol=None):
        self.success += 1
        # queue an affirmation every somany characters
        if self.success % Score.LINE_AFFIRM_THRESHOLD == 0:
            self.affirmation_queued = True
        if symbol and symbol == key.ENTER and self.affirmation_queued:
            self.affirmation_queued = False
            return True
    def miss(self):
        self.misses += 1
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
    def draw(self):
        scoretext = 'fail percentage: %s\nmisses: %s\ncps: %s' % (self.miss_rate(), self.misses, self.get_cps())
        pyglet.text.Label(scoretext, 
                       color=Colors.t('green'),
                       font_name='Consolas', 
                       font_size=10,
                       x=Screen.width, y=0,
                       anchor_y='bottom', anchor_x='right',
                       multiline = True,
                       width = Screen.width // 4,
                       halign='center').draw()

class SnippetMonger:
    def __init__(self):
        self.snipfiles = [file for file in os.listdir('.') if file.endswith('snp')]
        self.snippets = []
        for file in self.snipfiles:
            self.snippets += [s for s in open(file).read().split('|||||=====|||||') if len(s)]
        self.snippets.sort(lambda x,y: len(x)-len(y)) # Sort snippets by length
        print self.snippets
        self.current = 0
    def next(self):
        if self.current >= len(self.snippets):
            self.current = 1
            return CodeSnippet(self.snippets[0], clean=True)
        self.current += 1
        return CodeSnippet(self.snippets[self.current-1], clean=True)

class Game:
    def __init__(self):
        self.snippetmonger = SnippetMonger()
        self.reset()
        self.aff = None
    def reset(self):
        self.scorer = Score()
        self.new_word()
    def new_word(self):
        self.current_snippet = self.snippetmonger.next()
    def affirmation(self,strong=False):
        self.aff = Affirmation(strong)
    def tick(self,dt):
        if self.aff:
            alive = self.aff.tick(dt)
            if not alive: self.aff = None
    def draw(self):
        self.current_snippet.draw()
        self.scorer.draw()
        if self.aff:
            self.aff.draw()

window = pyglet.window.Window(caption = "code typer", width = Screen.width, height = Screen.height, resizable = True)
window.set_icon(pyglet.image.load('codetypericon.png'))
pyglet.gl.glClearColor(*Colors.black)
fps_display = pyglet.clock.ClockDisplay() if DEBUG else None
game = Game()    

def tick(dt):
    game.tick(dt)
# this is being stupid. it should animate smoothly at 60, do I have to do interpolation in draw() or what...?
pyglet.clock.schedule_interval(tick, 1/120.0)

@window.event
def on_draw():
    window.clear()
    game.draw()
    if fps_display: fps_display.draw()

@window.event
def on_key_press(symbol, modifiers):
    game.scorer.key()
    hit, winner = game.current_snippet.symbol_on(symbol)
    if winner: # beat a snippet, strong affirmation
        game.new_word()
        game.affirmation(True)
    elif hit:
        affirm = game.scorer.hit(symbol)
        if affirm: # did a line, weak affirmation
            game.affirmation(False)

@window.event
def on_text(text):
    if game.current_snippet.type_on(text):
        game.scorer.hit()
    else:
        game.scorer.miss()

if __name__ == '__main__':
    if '1.1' not in pyglet.version:
        print 'you need pyglet 1.1 beta 2 or greater'
        sys.exit()
    pyglet.app.run()