import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

st.title("Interactive session - homepage")


login, word_game, sound_game, attention, stroop, time_aware = st.tabs(["Identification", "GAME 1", "GAME 2", "GAME 3", "GAME 4", "GAME 5"])


# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

with login : 

    if 'submit0' not in st.session_state:
        st.session_state.submit0 = False

    if not st.session_state.submit0 : 
        username = st.text_input('username', placeholder = 'firstname.surname')

        if st.button('SUBMIT', key = 'submitted0') : 
            user_df = conn.read(worksheet = 'users')
            list_users = list(user_df['user-list'])
            if username in list_users : 
                st.write('name already taken')
            else : 
                user_df.loc[len(user_df.index)] = [username]
                st.write(user_df)
                user_df = conn.update(data=user_df, worksheet = 'users') 
                st.session_state.submit0 = True
                st.session_state.user = username
                st.rerun()
    
    if st.session_state.submit0 : 
        st.write('You are done with registration')


# GAME 1
with word_game : 

    if "words" not in st.session_state:
        st.session_state.words = []

    if "rerun" not in st.session_state:
        st.session_state.rerun = False

    if 'submit1' not in st.session_state:
        st.session_state.submit1 = False


    def listwords():
        word_list = ''
        for word in st.session_state.words : 
            word_list += f' {word}'

        st.write(word_list)

    if not st.session_state.submit1 : 
        if st.session_state.rerun == True:
            st.session_state.rerun = False
            st.rerun()

        else:
            w = st.text_input('Enter words here', value="", placeholder = 'Enter a word')
            if st.button('Add word'):
                if w != "":
                    st.session_state.words.append(w)       

        listwords()

        if st.button('SUBMIT', key = 'submitted1') : 
            st.session_state.submit1 = True
            word_df = conn.read(worksheet = 'game1')
            for word in st.session_state.words : 
                i = list(word_df.index[word_df.WORD == word])
                if len(i) == 1 : 
                    word_df.loc[i[0], 'COUNT'] += 1
            word_df = conn.update(data=word_df, worksheet = 'game1') 
            st.rerun()
    
    if st.session_state.submit1 : 
        st.write('You are done with game 1')


with sound_game : 

    
    if 'submit2' not in st.session_state:
        st.session_state.submit2 = False


    if not st.session_state.submit2 : 
        amplitudes = [0 for _ in range (10)]
        for s in range (10) : 
            amp = st.slider(f'Sound {s+1}', min_value = 1, max_value = 10, key = f'amp_{s}')
            amplitudes[s] = amp


        if st.button('SUBMIT', key = 'submitted2') : 
            st.session_state.submit2 = True
            sound_df = conn.read(worksheet = 'game2')
            sound_df[st.session_state.user] = amplitudes         
            sound_df = conn.update(data=sound_df, worksheet = 'game2')
            st.rerun()
    
    if st.session_state.submit2 : 
        st.write('You are done with game 2')

with attention : 

    dt = 2
    
    
    if "letter_count" not in st.session_state:
        st.session_state.letter_count = 0

    if 'started' not in st.session_state:
        st.session_state.started = False

    if 'finished' not in st.session_state:
        st.session_state.finished = False


    def x_click() : 
        st.session_state.x_clicks[st.session_state.letter_index] = time.time()
    
    def not_x_click() : 
        st.session_state.not_x_clicks[st.session_state.letter_index] = time.time()

    if not st.session_state.started and not st.session_state.finished:

        if st.button('initialisation', key = 'init3') : 
            attention_df = conn.read(worksheet = 'game3s')
            st.session_state.letters = attention_df['LETTER']

        if st.button("Start", key = 'st3'):
            st.session_state.started = True
            st.session_state.start_time = time.time()
            st.session_state.letter_index = 0
            
            letters = st.session_state.letters

            if "x_clicks" not in st.session_state:
                st.session_state.x_clicks = [None for _ in range (len(letters))]
            
            if "not_x_clicks" not in st.session_state:
                st.session_state.not_x_clicks = [None for _ in range (len(letters))]
                
            st.rerun()

    if st.session_state.started and not st.session_state.finished :
        letters = st.session_state.letters
        count = st_autorefresh(interval=100, limit=int(10*dt*len(letters)+5), key="refresher")
        elapsed = time.time() - st.session_state.start_time
        st.session_state.letter_index = int(elapsed // dt)

        if st.session_state.letter_index < len(letters):
            letter = letters[st.session_state.letter_index]
            st.write(letter)             

            st.button("Click if X", on_click = x_click, key = 'clickx')
            st.button("Click if not X", on_click = not_x_click, key = 'clicknotx')

        else:
            success = [None for _ in range (len(letters))]
            rts = [None for _ in range (len(letters))]

            times_letters = [st.session_state.start_time+i*dt for i in range (len(letters))]

            for k in range (len(letters)) : 
                xt = st.session_state.x_clicks[k]
                not_xt = st.session_state.not_x_clicks[k]
                lt = times_letters[k]
    
                if  xt != None and not_xt == None : 
                    rts[k] = xt - lt
                    if letters[k] == 'X' : 
                        success[k] = 1
                    else : 
                        success[k] = 0

                elif xt == None and not_xt != None : 
                    rts[k] = not_xt - lt
                    if letters[k] != 'X' : 
                        success[k] = 1
                    else : 
                        success[k] = 0

            st.session_state.success = success
            st.session_state.rts = rts

            if st.button('submit results') : 
                attention_df = conn.read(worksheet = 'game3s')
                attention_df[st.session_state.user] = success         
                attention_df = conn.update(data=attention_df, worksheet = 'game3s')

                attention_df = conn.read(worksheet = 'game3t')
                attention_df[st.session_state.user] = rts   
                attention_df = conn.update(data=attention_df, worksheet = 'game3t') 
            
                st.session_state.finished = True
            
                st.rerun()

        
    if st.session_state.finished : 
        
            
        st.write('You are done with game 3')
        # st.write(st.session_state.success)
        # st.write(st.session_state.rts)


with stroop : 

    dt = 2
    list_colors = ['red', 'green', 'blue', 'yellow']
    
    if 'started4' not in st.session_state:
        st.session_state.started4 = False

    if 'finished4' not in st.session_state:
        st.session_state.finished4 = False


    def color_click(c) : 
        st.session_state.color_clicks[color][st.session_state.color_index] = time.time()
    

    if not st.session_state.started4 and not st.session_state.finished4:

        if st.button('initialisation', key = 'init4') : 
            stroop_df = conn.read(worksheet = 'game4s')
            st.session_state.names = stroop_df['NAME']
            st.session_state.colors = stroop_df['COLOR']

        if st.button("Start", key = 'st4'):
            st.session_state.started4 = True
            st.session_state.start_time4 = time.time()
            st.session_state.color_index = 0
            
            names = st.session_state.names
            colors = st.session_state.colors

            st.session_state.color_clicks = {color : [None for _ in range (len(names))] for color in list_colors}
            
            st.rerun()

    if st.session_state.started4 and not st.session_state.finished4 :
        names = st.session_state.names
        colors = st.session_state.colors

        count = st_autorefresh(interval=100, limit=int(10*dt*len(names)+5), key="refresher4")
        elapsed = time.time() - st.session_state.start_time4
        st.session_state.color_index = int(elapsed // dt)

        if st.session_state.color_index < len(names):
            word = names[st.session_state.color_index]
            color = colors[st.session_state.color_index]
            st.write(f':{color}[{word}]')             

            for color_option in list_colors : 
                st.button(color_option, on_click = color_click, args = [color_option])


        else:
            success = [0 for _ in range (len(names))]
            rts = [None for _ in range (len(names))]

            times_colors = [st.session_state.start_time4+i*dt for i in range (len(names))]
            clicks = st.session_state.color_clicks

            for k in range (len(names)) : 

                color = names[k]

                if clicks[color][k] != None : 
                    success[k] = 1 
                    rts[k] = clicks[color][k] - times_colors[k]
                
                else : 
                    for c in list_colors : 
                        if clicks[c][k] != None : 
                            rts[k] = clicks[c][k] - times_colors[k]
                

            st.session_state.success4 = success
            st.session_state.rts4 = rts

            if st.button('submit results') : 
                stroop_df = conn.read(worksheet = 'game4s')
                stroop_df[st.session_state.user] = success         
                stroop_df = conn.update(data=stroop_df, worksheet = 'game4s')

                stroop_df = conn.read(worksheet = 'game4t')
                stroop_df[st.session_state.user] = rts   
                stroop_df = conn.update(data=stroop_df, worksheet = 'game4t') 
            
                st.session_state.finished4 = True
            
                st.rerun()

        
    if st.session_state.finished4 : 
        
            
        st.write('You are done with game 4')
        # st.write(st.session_state.success4)
        # st.write(st.session_state.rts4)



with time_aware : 

    
    if 'started5' not in st.session_state:
        st.session_state.started5 = False

    if 'finished5' not in st.session_state:
        st.session_state.finished5 = False

    if 'submitted5' not in st.session_state:
        st.session_state.submitted5 = False


    def stop_click() : 
        delta = time.time() - st.session_state.start_time5
        st.session_state.stop_click = delta
        st.session_state.finished5 = True
    

    if not st.session_state.started5 and not st.session_state.finished5 :


        if st.button("Start", key = 'st5'):
            st.session_state.started5 = True
            st.session_state.start_time5 = time.time()

            st.session_state.stop_click = None
            
            st.rerun()

    if st.session_state.started5 and not st.session_state.finished5 :
        
        st.button('STOP', on_click = stop_click)
    

    if st.session_state.finished5 and not st.session_state.submitted5 : 

        st.write(f'{int(st.session_state.stop_click)} seconds have passed')

        if st.button('submit results') : 
            aware_df = conn.read(worksheet = 'game5')
            aware_df[st.session_state.user] = st.session_state.stop_click         
            aware_df = conn.update(data=aware_df, worksheet = 'game5')
            st.session_state.submitted5 = True
            st.rerun()

    if st.session_state.submitted5 : 

        st.write('You are done with game 5')

            
            