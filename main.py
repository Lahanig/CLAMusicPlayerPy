import asyncio, aioconsole, keyboard, colorama
import os, sys, json, platform
from pygame import mixer
from colorama import Fore, Back, Style

mixer.init()
colorama.init()

class Player:
    def __init__(self):
        self.platform = platform.system()
        self.base_path_flag = False
        self.application_path = ''
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
            os.chdir(self.application_path)
        else:
            app_full_path = os.path.realpath(__file__)
            self.application_path = os.path.dirname(app_full_path)
        if self.base_path_flag == True:
            self.application_path = self.application_path[:-4]

        self.custom_music_path = ''

        self.isActiveQuery = False
        self.query = ""

        self.colors = False
        self.main_text_color = ''
        self.active_text_color = ''

        self.volume = 0.01
        self.isPlayng = False
        self.isPaused = False

        self.system_text = ''
        self.playlists_list_str = ''
        self.track_list_str = ''

        self.temp_timer = 0

        self.track_list = []
        self.playlist_list = []

        self.current_track = ""
        self.current_track_id = 0
        self.current_track_name = ""
        self.current_track_position = 0
        self.current_track_position_skip_value = 0
        self.current_track_position_text = ''

        self.current_playlist = ""
        self.current_playlist_id = 0
        self.current_playlist_name = ""

        self.track_length = ''
        self.settings_file_path = ''
        self.settings_file_template = ''
        
        self.base_audio_dir_path = ""
        self.isQuery = False
        self.isStartLoop = False

        self.main_p = None
        self.query_p = None
        self.timer_p = None
        self.next_p = None
        self.pos_counter_p = None
        self.base_processes_p = None
        self.keyboard_survey_p = None

        self.next_f = False

        self.isDevBuild = False
    
    def _init_base_path(self):
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
            os.chdir(self.application_path)
        else:
            app_full_path = os.path.realpath(__file__)
            self.application_path = os.path.dirname(app_full_path)
        if self.base_path_flag == True:
            self.application_path = self.application_path[:-4]
        
        self.settings_file_path = str(self.application_path) + "/bin/settings.json"

    def _init_colors(self):
        if os.path.exists(self.settings_file_path) == True:
            f = open(self.settings_file_path)
            data = json.load(f)
            self.colors = data['colors']
            f.close()
        else:
            mixer.music.set_volume(0.01)
            self.volume = mixer.music.get_volume()
            self.set_settings_file_template()
            f = open(self.settings_file_path, "a")
            f.write(self.settings_file_template)
            f.close()
        
        if self.colors == True:
            self.main_text_color = Fore.LIGHTMAGENTA_EX
            self.active_text_color = Fore.CYAN
        else:
            self.main_text_color = Fore.RESET
            self.active_text_color = Fore.RESET

    def _init_volume_settings(self):
        f = open(self.settings_file_path)
        data = json.load(f)
        mixer.music.set_volume(data['volume'])
        f.close()
        self.volume = mixer.music.get_volume()

    def _init_music_path(self):
        with open(self.settings_file_path, encoding='utf-8') as fh:
            data = json.load(fh)
            self.custom_music_path = data['custom-music-path']
        
        if self.custom_music_path == '':
            if os.path.exists(str(self.application_path) + '/assets/audio/') == True:
                self.base_audio_dir_path = str(self.application_path) + '/assets/audio/'
            else:
                os.makedirs(str(self.application_path) + '/assets/audio/')
                self.base_audio_dir_path = str(self.application_path) + '/assets/audio/'
        else:
            if os.path.exists(str(self.custom_music_path) + '/audio/') == True:
                self.base_audio_dir_path = str(self.custom_music_path) + '/audio/'
            else:
                os.makedirs(str(self.custom_music_path) + '/audio/')
                self.base_audio_dir_path = str(self.custom_music_path) + '/audio/'

    def _init_playlists(self):
        self.playlist_list = []
        tempPathVar = ''
        if self.custom_music_path == '':
            tempPathVar = self.application_path + '/assets/'
        else: 
            tempPathVar = self.custom_music_path
        for playlist in os.listdir(tempPathVar):
            if os.path.isdir(tempPathVar + '/' + playlist) == True:
                self.playlist_list.append(playlist)
        self.playlists_list_str = ''
        i = 0
        for playlist in self.playlist_list:
            self.playlists_list_str += str(i) + '. ' + playlist + '\n'
            i += 1
        
    def _init_tracks(self):
        self.track_list = []
        if self.current_playlist_id != 0:
            if self.custom_music_path == '':
                self.base_audio_dir_path = self.application_path + '/assets/' + self.current_playlist_name + '/'
            else:
                self.base_audio_dir_path = self.custom_music_path + '/' + self.current_playlist_name + '/'
        for track in os.listdir(self.base_audio_dir_path):
            if track.lower().endswith(('.mp3', '.wav')):
                self.track_list.append(track)
        self.track_list_str = ''
        i = 0
        for track in self.track_list:
            if track.find('.mp3') != -1 or track.find('.wav') != -1:
                track = track[:-4]
            self.track_list_str += str(i) + '. ' + track + '\n'
            i += 1

    async def update_track_position(self):
        self.current_track_position = (mixer.music.get_pos() / 1000)
        if int(round(self.current_track_position)) + self.current_track_position_skip_value >= int(round(self.track_length)):
            self.current_track_position = 0
            self.current_track_position_skip_value = 0
            self.next_f = True
            self.pos_counter_p.cancel()
            return 0
        else:
            self.pos_counter_p.cancel()
            self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')

    async def anext(self):
        self.next_p.cancel()
        if self.next_f == True:
            self.next_f = False
            if len(self.track_list)-1 > self.current_track_id:
                self.main_p.cancel()
                for task in asyncio.all_tasks():
                    task.cancel()
                return self.comand('choose_track', 3, value=self.current_track_id + 1, flag=True)
            else:
                return self.comand('close_track')
        else: self.next_p = asyncio.create_task(self.anext(), name="next_process")

    def set_settings_file_template(self):
        self.settings_file_template = '{"colors": '+ json.dumps(self.colors) + ', ' + '"volume": '+ json.dumps(self.volume) + ', ' + '"custom-music-path": '+ json.dumps(self.custom_music_path) +'}'

    async def timer(self, value, display):
        self.comand("update", display)
        await asyncio.sleep(value)
        self.current_track_position_text = ''
        self.comand("update", display)
        self.timer_p.cancel()

    def terminate_base_processes(self):
        self.main_p.cancel()
        if self.pos_counter_p != None and self.next_p != None:
            self.pos_counter_p.cancel()
            self.next_p.cancel()
            #self.keyboard_survey_p.cancel()

    def flush_input(self):
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        except ImportError:
            import sys, termios    # for linux/unix
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)

    async def linux_keyboard_survey(self):
        from curtsies import Input
        with Input() as input_generator:
            for c in input_generator:
                # repr(e)
                # print(c)
                if self.isQuery == False:
                    if c == '<Esc+b>':
                        self.isQuery = True
                        self.query = "b"
                    elif c == '<Esc+p>':
                         self.isQuery = True
                         self.query = "p"
                    elif c == '<Esc+d>':
                         self.isQuery = True
                         self.query = "d"
                    elif c == "u" or c == "<Esc+u>":
                         self.isQuery = True
                         self.query = "u"
                    elif c == "<Esc+v>":
                         self.isQuery = True
                         self.query = "cp"
                    elif c == "<Esc+c>":
                         self.isQuery = True
                         self.query = "vc"
                    elif c == "<Esc+s>":
                         self.isQuery = True
                         self.isActiveQuery = True
                self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
                self.next_p = asyncio.create_task(self.anext(), name="next_process")
                break
        self.keyboard_survey_p.cancel()

    def print_base_display_text(self, display):
        os.system("cls||clear")

        self._init_colors()
        self._init_volume_settings()

        self._init_music_path()
        self._init_playlists()
        self._init_tracks()

        match display:
            case 0:
                print(self.main_text_color + "CLA Music Player")
                print('Enter p - to play music | exit - to close application')
                print(self.system_text)
            case 1:
                print(self.main_text_color + "Is playng: " + self.current_track_name)
                print('Enter b - to close music | p - to pause music | up - to resuming music')
                print("Current track length: " + self.active_text_color + str(int(round(self.track_length))) + "s " + self.main_text_color + 
                self.current_track_position_text + "\n" + "Current track ID: " + self.active_text_color + str(self.current_track_id) + "\n" + self.main_text_color + str(self.system_text))
            case 2:
                print(self.main_text_color + "Select playlist")
                print('Enter p 0 - to open base playlist | b - to back on start display')
                print(str(self.system_text) + '\n' + self.playlists_list_str)
            case 3:
                print(self.main_text_color + "Playlist " + self.current_playlist_name)
                print('Enter p {id} - to play track with {id} | b - to back on select playlist display\n')
                print(str(self.system_text) + 'Tracks in this playlist:' + '\n' + self.track_list_str)
    
    async def player_query(self, flag=False):
        self.query = ""
        self.query = await asyncio.create_task(aioconsole.ainput('>>> ' + self.active_text_color), name="query_task")
        if flag == True:
            mixer.music.unpause()
            self.current_track_position_text = ""
            self.comand('update', 1)

    async def start(self):
        self._init_base_path()
        self.print_base_display_text(0)
        
        await self.player_query()

        if self.query == "p".lower() or self.query == "play".lower():
            self.main_p = asyncio.ensure_future(self.select_playlist_loop())
            self.main_p.set_name('main_process')
        elif self.query == "colors".lower():
            self.comand("colors")
            self.main_p = asyncio.ensure_future(self.start())
            self.main_p.set_name('main_process')
        elif self.query == "check volume".lower() or self.query == "vc".lower():
            return self.comand("check_volume")
        elif self.query == "update".lower() or self.query == "u".lower():
            self.comand("update")
            self.main_p = asyncio.ensure_future(self.start())
            self.main_p.set_name('main_process')
        elif self.query.find("set volume ".lower()) != -1: 
            vol = float(self.query[11:])
            return self.comand("set_volume", value=vol)
        elif self.query == "exit".lower():
            print(Style.RESET_ALL + " ")
            os.system("cls||clear")
            os._exit(0)
        else:
            self.main_p = asyncio.ensure_future(self.start())
            self.main_p.set_name('main_process')

    async def select_playlist_loop(self):
        # self.system_text = asyncio.all_tasks()
        self.print_base_display_text(2)
        
        await self.player_query()

        if self.query.find("p ".lower()) != -1:
            try: 
                playlist_id = int(self.query[2:])
                return self.comand('choose_playlist', 3, value=playlist_id)
            except:
                self.main_p = asyncio.ensure_future(self.select_playlist_loop())
        else:
            match self.query.lower():
                case 'c':
                    self.main_p = asyncio.ensure_future(self.start())
                case 'b':
                    self.main_p = asyncio.ensure_future(self.start())
                case 'exit':
                    print(Style.RESET_ALL + " ")
                    os.system("cls||clear")
                    os._exit(0)
                case other:
                    self.main_p = asyncio.ensure_future(self.select_playlist_loop())

    async def playlist_loop(self):
        # self.system_text = asyncio.all_tasks()
        self.print_base_display_text(3)
        await self.player_query()

        for task in asyncio.all_tasks():
            task.cancel()

        if self.query.find("p ".lower()) != -1:
            try:
                track_id = int(self.query[2:])
                return self.comand('choose_track', 3, value=track_id)
            except:
                self.main_p = asyncio.ensure_future(self.playlist_loop())
        else:
            match self.query.lower():
                case 'c':
                    self.main_p = asyncio.ensure_future(self.select_playlist_loop())
                case 'b':
                    self.main_p = asyncio.ensure_future(self.select_playlist_loop())
                case 'exit':
                    print(Style.RESET_ALL + " ")
                    os.system("cls||clear")
                    os._exit(0)
                case other:
                    self.main_p = asyncio.ensure_future(self.playlist_loop())

    async def track_loop(self):
        if self.platform == "Windows":
           if self.isQuery == False:
                if keyboard.is_pressed("alt+x"):
                    self.isQuery = True
                    self.query = "b"
                elif keyboard.is_pressed("alt+p"):
                    self.isQuery = True
                    self.query = "p"
                elif keyboard.is_pressed("alt+b"):
                    self.isQuery = True
                    self.query = "back"
                elif keyboard.is_pressed("alt+n"):
                    self.isQuery = True
                    self.query = "n"
                elif keyboard.is_pressed("u") or keyboard.is_pressed("alt+u"):
                    self.isQuery = True
                    self.query = "u"
                elif keyboard.is_pressed("alt+v"):
                    self.isQuery = True
                    self.query = "vc"
                elif keyboard.is_pressed("esc+d"):
                    self.isQuery = True
                    self.query = "d"
                elif keyboard.is_pressed("alt+c"):
                    self.isQuery = True
                    self.query = "cp"
                elif keyboard.is_pressed("alt+s"):
                    self.isQuery = True
                    mixer.music.pause()
                    self.current_track_position_text = "| Current track position: " + self.active_text_color + str(int(round(self.current_track_position)) + self.current_track_position_skip_value) + "s" + self.main_text_color
                    self.comand('update', 1)
                    self.flush_input()
                    await self.player_query()
                    # self.query = input(">>> " + self.active_text_color)
                    mixer.music.unpause()
                    self.current_track_position_text = ""
                    self.comand('update', 1)
        else:
            self.keyboard_survey_p = asyncio.create_task(self.linux_keyboard_survey(), name="keyboard_survey_process")

        if self.isActiveQuery == True:
            mixer.music.pause()
            self.current_track_position_text = "| Current track position: " + self.active_text_color + str(int(round(self.current_track_position)) + self.current_track_position_skip_value) + "s" + self.main_text_color
            self.system_text = asyncio.all_tasks()

            self.comand('update', 1)
            self.print_base_display_text(1)
            # self.flush_input()
            await self.player_query()

            mixer.music.unpause()
            self.current_track_position_text = ""

            self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
            self.next_p = asyncio.create_task(self.anext(), name="next_process")

            self.comand('update', 1)
            self.isQuery = False
            self.isActiveQuery = False

        match self.query.lower():
            case "p":
                self.query = ""
                await asyncio.sleep(0.2)
                self.terminate_base_processes()
                return self.comand("pause")
            case "back":
                self.query = ""
                await asyncio.sleep(0.2)
                self.terminate_base_processes()
                return self.comand("back_to_previos_track")
            case "n":
                self.query = ""
                await asyncio.sleep(0.2)
                self.terminate_base_processes()
                return self.comand("next_track")
            case "up":
                self.query = ""
                await asyncio.sleep(0.2)
                self.terminate_base_processes()
                return self.comand("unpause")
            case "vc":
                self.query = ""
                await asyncio.sleep(0.2)
                self.terminate_base_processes()
                return self.comand("check_volume", 1)
            case "c":
                self.query = ""
                await asyncio.sleep(0.2)
                self.terminate_base_processes()
                return self.comand("close_track")
            case "d":
                self.query = ""
                await asyncio.sleep(0.2)
                self.terminate_base_processes()
                return self.comand("debug")
            case 'b':
                self.query = ""
                await asyncio.sleep(0.2)
                self.terminate_base_processes()
                return self.comand("close_track")
            case "u":
                self.query = ""
                await asyncio.sleep(0.2)
                self.comand("update", 1)
            case "cp":
                self.query = ""
                await asyncio.sleep(0.2)
                self.comand("check_pos")
            
        if self.query.find("vs ".lower()) != -1:
            vol = float(self.query[3:])

            self.query = ""
            await asyncio.sleep(0.2)
            self.terminate_base_processes()
            return self.comand("set_volume", 1, value=vol)
        elif self.query.find("s ".lower()) != -1:
            sec = float(self.query[2:])

            self.query = ""
            await asyncio.sleep(0.2)
            self.terminate_base_processes()
            return self.comand("skip_pos", 1, value=sec)
        
        await asyncio.sleep(0.07)

        self.main_p = asyncio.ensure_future(self.track_loop())
        self.main_p.set_name('main_process')

    def comand(self, comand, display=0, value=0.01, flag=False): 
        self.system_text = ""
        match comand:
            case "debug":
                self.isQuery = False

                if self.isDevBuild == True:
                    self.system_text = asyncio.all_tasks()

                self.print_base_display_text(1)

                self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
                self.next_p = asyncio.create_task(self.anext(), name="next_process")

                self.main_p = asyncio.ensure_future(self.track_loop())
                self.main_p.set_name('main_process')
            case "update":
                self.isQuery = False
                self.print_base_display_text(display)
            case "play":
                self.isQuery = False
                self.isPlayng == False
                
                mixer.music.play(loops=0)
                self.print_base_display_text(1)

                # self.terminate_base_processes()

                self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
                self.next_p = asyncio.create_task(self.anext(), name="next_process")

                self.main_p = asyncio.ensure_future(self.track_loop())
                self.main_p.set_name('main_process')
                
                if flag == True:
                    if self.platform != "Windows":
                        # self.comand("pause")
                        # self.comand("pause")
                        pass
            case "close_track":
                self.isQuery = False
                mixer.music.stop()

                self.current_track_position = 0
                self.current_track_position_skip_value = 0

                self.main_p.cancel()
                for task in asyncio.all_tasks():
                    task.cancel()
                
                self.flush_input()
                if flag == False:
                    self.print_base_display_text(3)
                    self.main_p = asyncio.ensure_future(self.playlist_loop())
                else:
                    flag = False
                    for task in asyncio.all_tasks():
                        task.cancel()
                    self.comand('choose_track', 3, value=self.current_track_id + 1)
            case "pause":
                self.isQuery = False
                match self.isPaused: 
                    case False:
                        mixer.music.pause()
                        self.isPaused = True
                        self.current_track_position_text = "| Current track position: " + self.active_text_color + str(int(round(self.current_track_position)) + self.current_track_position_skip_value) + "s" + self.main_text_color
                    case True: 
                        mixer.music.unpause()
                        self.isPaused = False
                        self.current_track_position_text = ""
                
                self.comand('update', 1)

                self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
                self.next_p = asyncio.create_task(self.anext(), name="next_process")
                
                self.main_p = asyncio.ensure_future(self.track_loop())
                self.main_p.set_name('main_process')
            case "unpause":
                self.isQuery = False

                mixer.music.unpause()
                self.isPaused = False

                self.current_track_position_text = ""
                self.comand('update', 1)

                self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
                self.next_p = asyncio.create_task(self.anext(), name="next_process")

                self.main_p = asyncio.ensure_future(self.track_loop())
                self.main_p.set_name('main_process')
            case "colors":
                match self.colors:
                    case False:
                        self.main_text_color = Fore.LIGHTMAGENTA_EX
                        self.active_text_color = Fore.CYAN

                        print(self.main_text_color)
                        self.system_text = f'''{self.active_text_color}Colors is activated!{self.main_text_color}'''
                        self.colors = True
                    case True:
                        self.main_text_color = Fore.RESET
                        self.active_text_color = Fore.RESET

                        print(self.main_text_color)
                        self.system_text = f'''{self.active_text_color}Colors is deactivated!{self.main_text_color}'''
                        self.colors = False
            
                self.set_settings_file_template()
                f = open(self.settings_file_path, "w")
                f.write(self.settings_file_template)
                f.close()

            case "check_volume":
                self.isQuery = False
                self.volume = mixer.music.get_volume()
                self.system_text = f'''{self.active_text_color}Current volume is: {self.volume}{self.main_text_color}'''

                self.print_base_display_text(1)

                match display:
                    case 0:
                        self.main_p = asyncio.ensure_future(self.start())
                    case 1:
                        display = 0
                        self.isPlayng = False

                        self.print_base_display_text(1)

                        self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
                        self.next_p = asyncio.create_task(self.anext(), name="next_process")

                        self.main_p = asyncio.ensure_future(self.track_loop())
                        self.main_p.set_name('main_process')
            case "set_volume":
                self.isQuery = False

                mixer.music.set_volume(value)
                self.volume = mixer.music.get_volume()
                self.set_settings_file_template()

                f = open(self.settings_file_path, "w")
                f.write(self.settings_file_template)
                f.close()

                self.comand("check_volume", display)
            case "skip_pos":
                self.isQuery = False
                mixer.music.play(0, value)

                self.current_track_position = (mixer.music.get_pos() / 1000)
                self.current_track_position_skip_value = value + int(round(self.current_track_position))

                if self.isPaused == True:
                    mixer.music.pause()

                self.comand("update", 1)

                self.main_p.cancel()
                if self.pos_counter_p != None and self.next_p != None:
                    self.pos_counter_p.cancel()
                    self.next_p.cancel()
                
                self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
                self.next_p = asyncio.create_task(self.anext(), name="next_process")

                self.main_p = asyncio.ensure_future(self.track_loop())
                self.main_p.set_name('main_process')
            case "check_pos":
                self.isQuery = False
                self.current_track_position_text = "| Current track position: " + self.active_text_color + str(int(round(self.current_track_position)) + self.current_track_position_skip_value) + "s" + self.main_text_color
                self.timer_p = asyncio.ensure_future(self.timer(1, 1))
            case "choose_playlist":
                self._init_playlists()
                
                self.current_playlist_id = int(value)
                self.current_playlist_name = self.playlist_list[self.current_playlist_id]

                self.main_p = asyncio.ensure_future(self.playlist_loop())
            case "choose_track":
                self.isQuery = False
                self._init_tracks()

                self.current_track_id = int(value)

                if len(self.track_list) - 1 <= self.current_track_id:
                    mixer.music.load(self.base_audio_dir_path + self.track_list[len(self.track_list) - 1])
                    self.current_track = mixer.Sound(self.base_audio_dir_path + self.track_list[len(self.track_list) - 1])
                    self.track_length = self.current_track.get_length()

                    value = len(self.track_list) - 1
                    self.current_track_id = value
                elif int(value) >= 1:
                    mixer.music.load(self.base_audio_dir_path + self.track_list[int(value)])
                    self.current_track = mixer.Sound(self.base_audio_dir_path + self.track_list[int(value)])
                    self.track_length = self.current_track.get_length()
                else:
                    mixer.music.load(self.base_audio_dir_path + self.track_list[0])
                    self.current_track = mixer.Sound(self.base_audio_dir_path + self.track_list[0])
                    self.track_length = self.current_track.get_length()

                    value = 0
                    self.current_track_id = value

                self.current_track_name = self.track_list[self.current_track_id]
                if self.current_track_name.find('.mp3') != -1 or self.current_track_name.find('.wav') != -1:
                    self.current_track_name = self.track_list[int(value)][:-4]

                value = 0.01
                
                self.main_p.cancel()
                if self.pos_counter_p != None and self.next_p != None:
                    self.pos_counter_p.cancel()
                    self.next_p.cancel()
                    # self.keyboard.cancel()

                self.pos_counter_p = asyncio.create_task(self.update_track_position(), name='position_counter_process')
                self.next_p = asyncio.create_task(self.anext(), name="next_process")

                if flag == True:
                    if self.platform != "Windows":
                        self.comand("play", flag=True)
                    else:
                        self.comand('play')
                else:
                    self.comand('play')
            case "next_track":
                self.comand('choose_track', 3, value=self.current_track_id + 1, flag=True)
            case "back_to_previos_track":
                self.comand('choose_track', 3, value=self.current_track_id - 1, flag=True)

    async def main(self):
        self.main_p = asyncio.ensure_future(self.start())
        self.main_p.set_name('main_process')

player = Player()

if __name__ == '__main__':
    player.isDevBuild = True

    run_app = asyncio.ensure_future(player.main())

    event_loop = asyncio.get_event_loop()
    event_loop.run_forever()