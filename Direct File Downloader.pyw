import os, ast, sys, requests, time
from tkinter import filedialog, messagebox
from tkinter import *
from tkinter.ttk import Progressbar, Style
from threading import Thread
from PIL import Image, ImageTk
import urllib.request

# download capacity in byte

# chunk_size =1024 #1kb
# chunk_size =10240 #10 kb
# chunk_size =102400 #100 kb
# chunk_size =1048576 #1024 kb

chunk_size =15360 #15 kb

url_datas =[]
url_length =0
downloads_window_popup =False

progressbar_length =400
frame_index =0

save_path =''

def window(width, height, x, y, title, icon=None, fixed_size=True, toplevel=False):
    if toplevel:
        window =Toplevel()
    else:
        window =Tk()
    if icon:
        window.iconbitmap(icon)
    window.title(title)
    window.geometry(str(width)+'x'+str(height)+'+'+str(x)+'+'+str(y))
    if fixed_size:
        window.minsize(width, height)
        window.maxsize(width, height)
    return window

def frame(window, width, height, bg, padx, pady, grid_row, grid_column, sticky):
    frame =Frame(window, width=width, height=height, bg=bg)
    frame.grid(row=grid_row, column=grid_column, padx=padx, pady=pady, sticky=sticky)
    return frame

def button(window, text, width, height, command, bg, fg, active_bg, active_fg, font, padx, pady, grid_row, grid_column, sticky):
    button =Button(window, text=text, width=width, height=height, font=font, command=command, bg=bg, fg=fg, activebackground=active_bg, activeforeground=active_fg)
    button.grid(row=grid_row, column=grid_column, padx=padx, pady=pady, sticky=sticky)
    return button

def label(window, text, width, height, bg, fg, font, padx, pady, grid_row, grid_column, sticky):
    label =Label(window, text=text, width=width, height=height, bg=bg, fg=fg, font=font)
    label.grid(row=grid_row, column=grid_column, padx=padx, pady=pady, sticky=sticky)
    return label

def entry(window, width, bg, fg, font, padx, pady, grid_row, grid_column, sticky):
    entry =Entry(window, width=width, bg=bg, fg=fg, font=font)
    entry.grid(row=grid_row, column=grid_column, padx=padx, pady=pady, sticky=sticky)
    return entry

def canvas(window, width, height, bg, padx, pady, grid_row, grid_column, sticky, responsive=True):
    if responsive:
        window.grid_rowconfigure(grid_row, weight=1)
        window.grid_columnconfigure(grid_column, weight=1)
    canvas =Canvas(window, width=width, height=height, bg=bg)
    canvas.grid(row=grid_row, column=grid_column, padx=padx, pady=pady, sticky=sticky)
    return canvas

def progressbar(window, length_size, padx, pady, grid_row, grid_column, sticky):
    progressbar =Progressbar(window, mode='determinate', orient='horizontal', length=length_size)
    progressbar.grid(row =grid_row, column=grid_column, padx=padx, pady=pady, sticky=sticky)
    return progressbar

def scrollbar(window, view, axis, padx, pady, grid_row, grid_column, sticky, responsive =True):    
    if responsive:
        window.grid_rowconfigure(grid_row, weight=1)
        window.grid_columnconfigure(grid_column, weight=1)
    if axis == 'X':
        scrollbar =Scrollbar(window, orient='horizontal')
        scrollbar.grid(row=grid_row, column=grid_column, padx=padx, pady=pady, sticky=sticky)
        xScrollbarConfig(scrollbar, view)
    else:
        scrollbar =Scrollbar(window, orient='vertical')
        scrollbar.grid(row=grid_row, column=grid_column, padx= padx, pady =pady, sticky=sticky)
        yScrollbarConfig(scrollbar, view)
    return scrollbar

def xScrollbarConfig(scroll_bar, view):
    scroll_bar.config(command=view.xview)
    view.config(xscrollcommand = scroll_bar.set)

def yScrollbarConfig(scroll_bar, view):
    scroll_bar.config(command=view.yview)
    view.config(yscrollcommand = scroll_bar.set)
    
def resource_path(file_name):
    try:
        base_path =sys._MEIPASS
    except Exception:
        base_path =os.path.abspath(".")
    return os.path.join(base_path, file_name)


def save_file_path():
    global save_path
    save_path =filedialog.askdirectory()

def url_file_size(url):
    file = urllib.request.urlopen(url)
    size =file.length
    if not size:
        size =0
    return int(size)

def downloader(data):
    file_name =data['file-name']
    save_path =data['save-path']
    url =data['url']
    total_size =data['total-size']
    data['downloading'] =True
    data['on_speed'] =''

    if total_size:
        file =open(save_path+'/'+file_name, 'ab')
    else:
        file =open(save_path+'/'+file_name, 'wb')

    if total_size:
        file_size =file.tell()
    else:
        file_size =0
    
    Thread(target=speed_miter, args=[file_size, save_path+'/'+file_name, data]).start()

    if file_size:
        headers ={}
        headers['Range'] = f'bytes={file_size}-'
        stream =requests.get(url, headers=headers, stream=True)
    else:
        stream =requests.get(url, stream=True)
    
    if total_size:
        per =total_size/progressbar_length
    else:
        total_size =0
        per =0
    
    for bytes_data in stream.iter_content(chunk_size):
        if data['operation']=='pause':
            data['progress'].configure(style='yellow.Horizontal.TProgressbar')
            break
        if total_size and total_size<=file_size:
            break
        if downloads_window_popup and per:
            value =int((file_size/total_size)*100)
            try:
                data['progress'].configure(style='green.Horizontal.TProgressbar')
                fill_progress(data['progress'], value)
            except Exception:
                pass
            data['progress-value'] =value
        elif downloads_window_popup:
            try:
                data['progress'].configure(style='blue.Horizontal.TProgressbar')
                fill_progress(data['progress'], 100)
            except Exception:
                pass
            data['progress-value'] =100
        file.write(bytes_data)

        file_size =file.tell()
        try:data['ss-label'].configure(text=Download_details(file_size, total_size, data))
        except Exception:pass
    
    file.close()
    print('file closed...')
    data['downloading'] =False

    if file_size>=total_size or not total_size:
        data['operation']='complete'
        data['progress'].destroy()
        data['sp-ico'].destroy()
        data['ss-label'].destroy()
        data['process-frame'].grid_columnconfigure(2, weight=1)
        # data['close-ico'].grid_configure(sticky='ew')
        data['close-ico'].config(bg='white')

def byte_to_memory(byte_size):
    if byte_size <=1024:
        return f'{byte_size:.0f}B'
    elif byte_size <=1024*1024:
        return f'{byte_size/1024:.0f}Kb'
    elif byte_size <=1024*1024*1024:
        return f'{byte_size/1024/1024:.1f}Mb'
    elif byte_size <=1024*1024*1024*1024:
        return f'{byte_size/1024/1024/1024:.2f}Gb'
    else:
        return f'{byte_size/1024/1024/1024/1024:.3f}Tb'

def speed_miter(oldsize, filepath, data):
    while data['downloading']:
        time.sleep(1)
        latestsize =os.stat(filepath).st_size
        avgsize =latestsize-oldsize
        data['on_speed'] =byte_to_memory(avgsize)+'ps'
        oldsize =latestsize

def Download_details(new_file_size, total_size, data):
    query =''
    if total_size:
        query+=f'{int((new_file_size/total_size)*100)}% {byte_to_memory(int(new_file_size))}/{byte_to_memory(int(total_size))} '
    else:
        query+=f'{byte_to_memory(int(new_file_size))}/Unknown '
    
    return query+' '+data['on_speed']

def fill_progress(progress, value):
    progress['value'] =value

def download():
    global save_path
    url =file_url.get()
    file =file_name.get()
    if not url:
        messagebox.showwarning('Warning', 'Required! Url..')
        return
    
    if not '://' in url:
        messagebox.showwarning('Warning', 'Enter Full Url..')
        return

    if not file:
        file =url.split('/')[-1]
        
    if not os.path.exists(save_path):
        save_path =os.curdir

    url_datas.append({
        'url':url,
        'file-name':file,
        'save-path':save_path,
        'total-size':url_file_size(url),
        'operation':'start',
        'downloading':False,
        'progress-value':0,
        'on_speed':''
        })
    downloads_window()

def get_length(url_datas):
    return len(url_datas)

def load_data():
    if os.path.exists('./configure/config'):
        data =open('./configure/config', 'r')
        result =data.read()
        data.close()
        if result:
            return ast.literal_eval(result)

def save_data(url_datas):
    if not os.path.exists('./configure'):
        os.mkdir('./configure')
    file =open('./configure/config', 'w')
    new_data =[]

    for data in url_datas:
        new_data.append(data.copy())

    for data in new_data:
        data['process-frame'] =None
        data['progress'] =None
        data['sp-ico'] =None
        data['ss-label'] =None
        data['close-ico'] =None
        data['downloading'] =False

    file.write(str(new_data))
    file.close()

def close_frame(data, frame):
    if not data['operation']=='complete':
        if not messagebox.askyesno('Warning', 'Do You Want Stop The Download?'):
            return
    if data['operation']=='play':
        data['operation']='pause'
    frame.destroy()
    for d in url_datas:
        if d==data:
            url_datas.remove(data)
            break
    del data

def change_process(data, s_ico, p_ico):
    process =data['operation']
    if process=='start':
        if not data['total-size']:
            if not messagebox.askyesno('Warning', 'You Can\'t Resume To Continue Download, Do You Want Pause?'):
                return
        data['sp-ico'].config(image=s_ico)
        data['sp-ico'].image =s_ico
        data['operation']='pause'
    else:
        data['sp-ico'].config(image=p_ico)
        data['sp-ico'].image =p_ico
        data['operation']='start'
        Thread(target=downloader, args=[data]).start()

def download_file_frame(window, grid_row, data):
    file_name =data['file-name'] 
    download_file_frame =frame(window, None, None, 'white', (10, 10), (10, 10), grid_row, 0, 'we')
    window.grid_columnconfigure(0, weight=1)
    label(download_file_frame, file_name, None, None, 'white', 'blue', ('bold', 15), (10, 0), 0, 0, 0, 'w')
    process_frame =frame(download_file_frame, None, None, 'white', 0, 0, 1, 0, 'ew')
    data['process-frame'] =process_frame
    if not data['operation']=='complete':
        progress =progressbar(process_frame, progressbar_length, (10, 0), (0, 10), 1, 0, None)
        data['progress'] =progress
        sp_ico =label(process_frame, '', None, None, None, None, None, (10, 10), (0, 10), 1, 1, None)
        data['sp-ico']=sp_ico
        ss_label =label(process_frame, 'Unknown', None, None, 'white', 'blue', ('bold', 12), 0, (0, 10), 1, 3, None)
        data['ss-label']=ss_label

    close_ico =label(process_frame, '', None, None, None, None, None, 0, (0, 10), 1, 2, None)
    data['close-ico']=close_ico
    download_file_frame.grid_columnconfigure(0, weight=1)
    
    if not data['operation']=='complete':
        image1 = Image.open(resource_path(".\images\play.png"))
        image1 =image1.resize((20, 20))
        s_ico = ImageTk.PhotoImage(image1)
        image2 = Image.open(resource_path(".\images\pause.png"))
        image2 =image2.resize((20, 20))
        p_ico = ImageTk.PhotoImage(image2)
    
    image3 = Image.open(resource_path(".\images\close.png"))
    image3 =image3.resize((20, 20))
    c_ico = ImageTk.PhotoImage(image3)

    close_ico.config(image=c_ico)
    close_ico.image =c_ico
    process =data['operation']
    if process=='start':
        sp_ico.config(image=p_ico)
        sp_ico.image =p_ico
        if not data['downloading']:
            Thread(target=downloader, args=[data]).start()
    elif process=='pause':
        sp_ico.config(image=s_ico)
        sp_ico.image =s_ico

    style =Style()
    style.theme_use('clam')

    # style.configure('red.Horizontal.TProgressbar', background='red')
    style.configure('yellow.Horizontal.TProgressbar', background='yellow')
    style.configure('green.Horizontal.TProgressbar', background='green')
    style.configure('blue.Horizontal.TProgressbar', background='blue')
    
    if data['total-size'] and data['operation']=='start':
        progress.configure(style='green.Horizontal.TProgressbar')
    elif data['operation']=='pause':
        progress.configure(style='yellow.Horizontal.TProgressbar')
    elif not data['total-size'] and data['operation']=='start':
        progress.configure(style='blue.Horizontal.TProgressbar')

    if not data['operation']=='complete':
        fill_progress(progress, data['progress-value'])

    if not data['operation']=='complete':
        sp_ico.bind('<Button-1>', lambda e: change_process(data, s_ico, p_ico))
    close_ico.bind('<Button-1>', lambda e: close_frame(data, download_file_frame))

    if data['operation']=='complete':
        process_frame.grid_columnconfigure(2, weight=1)
        close_ico.grid_configure(sticky='ew')
        close_ico.config(bg='white')

    return download_file_frame

def prepare_scrollable_frame(window):
    canvas1 = canvas(window, None, None, 'lightblue', 0, 0, 0, 0, 'nswe', False)
    vscrollbar = scrollbar(window, canvas1, 'Y', 0, 0, 0, 1, 'ns', True)

    canvas1.config(yscrollcommand=vscrollbar.set)

    frame2 = Frame(canvas1, background='lightblue')
    frame2_id = canvas1.create_window(0, 0, window=frame2, anchor=NW)

    def configure_frame2(event):
        size = (frame2.winfo_reqwidth(), frame2.winfo_reqheight())
        canvas1.config(scrollregion="0 0 %s %s" % size)
        if frame2.winfo_reqwidth() != canvas1.winfo_width():
            canvas1.config(width=frame2.winfo_reqwidth())
    frame2.bind('<Configure>', configure_frame2)

    def configure_canvas(event): 
        if frame2.winfo_reqwidth() != canvas1.winfo_width():
            canvas1.itemconfigure(frame2_id, width=canvas1.winfo_width())
    canvas1.bind('<Configure>', configure_canvas)
    return frame2

def downloads_window():
    global downloads_window_popup, downloadsWindow, frame_index
    if not downloads_window_popup:
        downloads_window_popup =True
    else:
        downloadsWindow.destroy()

    def destroy_now(window):
        global downloads_window_popup
        downloads_window_popup =False
        save_data(url_datas)
        window.destroy()

    def pack_frame(frame1, data):
        global frame_index
        download_file_frame(frame1, frame_index, data)
        frame_index+=1

    downloadsWindow =window(800, 400, 200, 100, 'Downloads', resource_path('.\images\logo.ico'), True, True)
    frame1 =prepare_scrollable_frame(downloadsWindow)
    
    frame_index =0
    for data in url_datas:
        pack_frame(frame1, data)
    
    save_data(url_datas)
    downloadsWindow.grid_rowconfigure(0, weight=1)
    downloadsWindow.grid_columnconfigure(0, weight=1)
    downloadsWindow.grid_columnconfigure(1, weight=0)
    downloadsWindow.protocol( 'WM_DELETE_WINDOW', lambda: destroy_now(downloadsWindow))
    downloadsWindow.mainloop()

def file_Downloader():
    global file_url, file_name
    Window =window(700, 350, 400, 200, 'Direct File Downloader', resource_path('.\images\logo.ico'))
    frame1 =frame(Window, None, None, 'lightblue', 0, 0, 0, 0, 'nswe')
    frame2 =frame(Window, None, None, 'lightblue', 0, 0, 1, 0, 'nswe')
    frame3 =frame(Window, None, None, 'lightblue', 0, 0, 2, 0, 'nswe')
    frame4 =frame(Window, None, None, 'lightblue', 0, 0, 3, 0, 'nswe')
    label(frame1, 'Direct File Downloader', None, None, 'lightblue', 'blue', ('bold', 20), (220, 0), (20, 0), 0, 0, None)
    label(frame2, 'File URL: ', None, None, 'lightblue', 'blue', ('bold', 15), (50, 0), (20, 0), 0, 0, None)
    file_url =entry(frame2, 50, 'lightblue', 'blue', ('bold', 13), (10, 0), (20, 0), 0, 1, None)
    label(frame2, 'Save File Name: ', None, None, 'lightblue', 'blue', ('bold', 15), (50, 0), (20, 0), 1, 0, None)
    file_name =entry(frame2, 50, 'lightblue', 'blue', ('bold', 13), (10, 0), (20, 0), 1, 1, None)
    button(frame3, 'Set Save File Path', 18, 2, save_file_path, 'lightblue', 'blue', 'blue', 'lightblue', ('bold', 13), (180, 0), (30, 0), 1, 0, None)
    button(frame3, 'Downloads', 17, 2, downloads_window, 'lightblue', 'blue', 'blue', 'lightblue', ('bold', 13), 0, (30, 0), 1, 1, None)
    button(frame4, 'Download', 30, 2, download, 'lightblue', 'blue', 'blue', 'lightblue', ('bold', 15), (180, 0), (20, 0), 2, 0, None)
    file_url.focus_set()
    # Window.overrideredirect(1)
    Window.config(bg='lightblue')
    Window.mainloop()

if __name__ == '__main__':
    if load_data():
        url_datas =load_data()
    file_Downloader()
