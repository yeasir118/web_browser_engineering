import tkinter
from url import URL, lex

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()

        self.window.bind("<Down>", self.on_down_key)
        self.window.bind("<Up>", self.on_up_key)

        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()

        self.scroll_y_index = 0
        self.lines_per_screen = int(HEIGHT / VSTEP)
    
    def on_down_key(self, event):
        if self.scroll_y_index + self.lines_per_screen <= self.scroll_y_max_index:
            self.scroll_y_index += 1
            self.draw()
    
    def on_up_key(self, event):
        if self.scroll_y_index > 0:
            self.scroll_y_index -= 1
            self.draw()
    
    def draw(self):
        screen_display_list = [item for item in self.display_list if (item[1] >= (VSTEP * (self.scroll_y_index + 1))) and (item[1] < (VSTEP * (self.scroll_y_index + self.lines_per_screen)))]
        self.canvas.delete("all")
        for x, y, c in screen_display_list:
            self.canvas.create_text(x, y - (VSTEP * (self.scroll_y_index)), text=c)

    def load(self, url):
        text = lex(url.request())
        
        self.display_list = layout(text)
        self.scroll_y_max_index = int(self.display_list[-1][1] / VSTEP) - 1 

        self.draw()
        
def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP

        if cursor_x + HSTEP >= WIDTH:
            cursor_x = HSTEP
            cursor_y += VSTEP
        
    return display_list

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()