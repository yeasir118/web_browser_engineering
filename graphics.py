import tkinter
import math
import argparse
from url import URL, lex

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
SCROLL_BAR_WIDTH = 15
SCROLL_BAR_OFFSET = 2
RIGHT_ALIGNED_CONTENT_OFFSET = 9

class Browser:
    def __init__(self, reverse=False):
        self.width = WIDTH
        self.height = HEIGHT

        self.reverse = reverse
        self.rightAlignedContentOffset = RIGHT_ALIGNED_CONTENT_OFFSET

        self.scrollStep = SCROLL_STEP
        self.scrollbarWidth = SCROLL_BAR_WIDTH
        self.scrollbarOffset = SCROLL_BAR_OFFSET

        self.window = tkinter.Tk()

        self.window.bind("<Configure>", self.resize_handler)
        self.window.bind("<Down>", self.scrolldown) 
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mouseScroll)

        self.canvas = tkinter.Canvas(
            self.window,
            width=self.width,
            height=self.height
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)

        self.scroll = 0
    
    def resize_handler(self, event):
        self.width = event.width
        self.height = event.height

        self.display_list = self.layout()
        self.draw()
    
    def mouseScroll(self, e):
        full_length = self.display_list[-1][1] if self.display_list else self.height
        if e.delta == -120 and self.scroll + self.height < full_length:
            self.scroll += self.scrollStep
            self.draw()
        elif e.delta == 120 and self.scroll > 0:
            self.scroll -= self.scrollStep
            self.draw()
    
    def scrolldown(self, e):
        full_length = self.display_list[-1][1] if self.display_list else self.height
        if self.scroll + self.height < full_length:
            self.scroll += self.scrollStep
        self.draw()
    
    def scrollup(self, e):
        if self.scroll > 0:
            self.scroll -= self.scrollStep
        self.draw()
    
    def drawScrollBarMini(self):
        top = (self.scroll / self.scrollStep) * self.scrollbarMiniScrollStep
        self.canvas.create_rectangle(self.width - self.scrollbarWidth + self.scrollbarOffset, top, self.width - self.scrollbarOffset, top + self.scrollbarMiniHeight)
    
    def drawScrollBar(self):
        self.canvas.create_rectangle(self.width - self.scrollbarWidth, 0, self.width, self.height)
    
    def draw(self):
        if not self.display_list:
            self.canvas.create_rectangle(0, 0, self.width, self.height)
            return
        self.canvas.delete("all")
        self.drawScrollBar()
        self.drawScrollBarMini()
        for x, y, c in self.display_list:
            if y > self.scroll + self.height: continue
            if y + VSTEP < self.scroll: continue

            self.canvas.create_text(x, y - self.scroll, text=c)

    def load(self, url_text):
        try:
            url = URL(url_text)
            body = url.request()
            self.text = lex(body)
        except:
            print(f"Error loading the url: {url_text}")
            self.text = ""
            self.display_list = []
            self.draw()
            return
        self.display_list = self.layout()
        self.draw()
        
    def layout(self):
        if not self.text:
            self.scrollbarMiniHeight = self.height
            self.scrollbarMiniScrollStep = 0
            return []
        
        display_list = []

        words = self.text.split(" ")
        cursor_x = HSTEP if not self.reverse else self.width - self.scrollbarWidth - self.rightAlignedContentOffset
        cursor_y = VSTEP
        step_sign = 1 if not self.reverse else -1

        for word in words:
            word = word[::-1] if self.reverse else word

            # word wrapping
            word_length = len(word) * HSTEP
            if (not self.reverse and cursor_x + word_length >= self.width - self.scrollbarWidth) \
                or (self.reverse and cursor_x - word_length <= 0):
                cursor_x = HSTEP if not self.reverse else self.width - self.scrollbarWidth - self.rightAlignedContentOffset
                cursor_y += VSTEP

            for c in word:
                display_list.append((cursor_x, cursor_y, c))
                cursor_x += (HSTEP * step_sign)

                # sentence wrapping
                # NOT NEEDED for English IF word wrapping is present
                # NEEDED for other languages EVEN IF word wrapping is present(like Chinese) where there are no word spacings 
                if (not self.reverse and cursor_x + HSTEP >= self.width - self.scrollbarWidth) \
                or (self.reverse and cursor_x - HSTEP <= 0):
                    cursor_x = HSTEP if not self.reverse else self.width - self.scrollbarWidth - self.rightAlignedContentOffset
                    cursor_y += VSTEP
            
            display_list.append((cursor_x, cursor_y, " "))
        
        full_length = display_list[-1][1] if display_list else self.height
        self.scrollbarMiniHeight = (self.height * self.height) / full_length
        
        if not display_list or full_length <= self.height:
            totalScrolls = 1
        else:
            totalScrolls = math.ceil(((full_length - self.height) / self.scrollStep))
        self.scrollbarMiniScrollStep = (self.height - self.scrollbarMiniHeight) / totalScrolls   

        return display_list

def reverse_words(text):
    text_list = text.split()
    for str in text_list:
        for c in str:
            print(c, end=" ")
        print("\n")


def main():
    parser = argparse.ArgumentParser(description="A simple browser with command line arguments")

    parser.add_argument("-r", "--reverse", action="store_true", help="Reverse the content of the page")
    parser.add_argument("url", type=str, help="The URL to load (e.g., http://example.com)")

    args = parser.parse_args()

    browser = Browser(reverse=args.reverse)
    browser.load(args.url)

    tkinter.mainloop()

if __name__ == "__main__":
    main()