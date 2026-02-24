import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from random import randint 

st.title("Interactive session - homepage")

tabs = ["Registration", "GAME 1", "GAME 2", "GAME 3", "GAME 4", "GAME 5"]
login, word_game, sound_game, attention, stroop, time_aware = st.tabs(tabs)


# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

if 'user' not in st.session_state:
    st.session_state.user = randint(0,1000)
    st.session_state.tab_step = [0 for _ in range (len(tabs))]
    st.session_state.trial =  0 



def initialisation_game(dict_state) : 
    for key in dict_state.keys() : 
        st.session_state[key] = dict_state[key] 
                        
@st.cache_data
def read_sheet(sheet) : 
    return conn.read(worksheet = sheet)

@st.cache_data
def write_sheet(sheet, df) : 
    return conn.update(data=df, worksheet = sheet) 


def save_click(game, label, position) : 
    if st.session_state[f"type_click_{game}"][position] is None : 
        st.session_state[f"type_click_{game}"][position] = label
        st.session_state[f"delay_{game}"][position] = time.time()

def restart(game, button = 'Restart?') : 

    if st.button(button, key = f'{game}_{st.session_state.trial}') : 
        st.session_state.tab_step[game] = 0 
        st.session_state.trial += 1
        st.rerun()


def over(title = 'this part') : 
    st.write(f'You are done with {title} {st.session_state.user}')


with login : 

    if st.session_state.tab_step[0] == 0 : 

        username = st.text_input('username', placeholder = 'firstname.surname')

        if st.button('SUBMIT', key = 'submitted0') : 
            user_df = read_sheet('users')
            list_users = list(user_df['user-list'])
            if username in list_users : 
                st.write('name already taken')
            else : 
                user_df.loc[len(user_df.index)] = [username]
                user_df = write_sheet('users', user_df)
                st.session_state.user = username
                st.session_state.tab_step[0] = 1
                st.rerun()

    else : 
        over('registration')
        restart(0, "Change username?")
        

# GAME 1
with word_game : 

    @st.cache_data
    def listwords(words):
        word_list = ''
        for word in words : 
            word_list += f' {word}'

        st.write(word_list)
    
    if st.session_state.tab_step[1] == 0 : 

        initialisation_game({'words' : []})

        with st.form('Words entry', clear_on_submit = True) : 
            w = st.text_input('Enter words here', value="", placeholder = 'Enter a word', key='user_word')

            if st.form_submit_button('Add word to list'):
                if w != "":
                    st.session_state.words.append(w)    
                    # st.session_state.user_word = ''  

            listwords(st.session_state.words)

        if st.button('Send word list', key = 'submitted1') : 
            word_df = read_sheet('game1')
            for word in st.session_state.words : 
                i = list(word_df.index[word_df.WORD == word])
                if len(i) == 1 : 
                    word_df.loc[i[0], 'COUNT'] += 1
            word_df = write_sheet('game1', word_df)
            st.session_state.tab_step[1] = 1
            st.rerun()
    
    else : 
        over("game 1")


with sound_game : 

    if st.session_state.tab_step[2] == 0 :  

        with st.form("Estimation of Sound Amplitudes") : 

            amplitudes = [0 for _ in range (10)]
            for s in range (10) : 
                amp = st.slider(f'Sound {s+1}', min_value = 1, max_value = 10, key = f'amp_{s}')
                amplitudes[s] = amp

            if st.form_submit_button('SUBMIT', key = 'submitted2') : 
                
                sound_df = read_sheet('game2')
                sound_df[st.session_state.user] = amplitudes         
                sound_df = write_sheet('game2', sound_df)
                st.session_state.tab_step[2] = 1
                st.rerun()
    
    else : 
        over('game 2')
        
        restart(2)

with attention : 

    dt = 2

    if st.session_state.tab_step[3] == 0 : 

        initialisation_game({"letter_count": 0})

        if st.button('initialisation', key = 'init3') : 
            
            attention_df = read_sheet('game3s')
            letters = attention_df['LETTER']
            initialisation_game({"letters" : letters, "type_click_3" : [None for _ in range (len(letters))], "delay_3" : [None for _ in range (len(letters))]})
            st.session_state.tab_step[3] = 1 
            st.rerun()

    elif st.session_state.tab_step[3] == 1 : 
        
        if st.button("Start", key = 'st3'):
            initialisation_game({"start_time" : time.time(), "letter_index" : 0})   
            st.session_state.tab_step[3] = 2 
            st.rerun()
    
    elif st.session_state.tab_step[3] == 2 :

        letters = st.session_state.letters
        count = st_autorefresh(interval=100, limit=int(10*dt*len(letters)+5), key="refresher")
        elapsed = time.time() - st.session_state.start_time
        st.session_state.letter_index = int(elapsed // dt)

        if st.session_state.letter_index < len(letters):
            letter = letters[st.session_state.letter_index]
            st.write(letter)             
            st.button("Click if X", on_click = save_click, args = [3, "X", st.session_state.letter_index], key = 'clickx')
            st.button("Click if not X", on_click = save_click, args = [3, "not_X", st.session_state.letter_index],  key = 'clicknotx')

        else:
            success = [1 if (letters[k] == "X" and st.session_state['type_click_3'] == "X") or (letters[k] != "X" and st.session_state['type_click_3'] == "not_X") else 0 for k in range (len(letters))]
            rts = st.session_state['delay_3']

            if st.button('submit results') : 
                attention_df = read_sheet('game3s')
                attention_df[st.session_state.user] = success         
                attention_df = write_sheet('game3s', attention_df)

                attention_df = read_sheet('game3t')
                attention_df[st.session_state.user] = rts         
                attention_df = write_sheet('game3t', attention_df)

                st.session_state.tab_step[3] = 3
                st.rerun()
        
    else : 
        over('game 3')
        
    restart(3)



with stroop : 

    dt = 2
    list_colors = ['red', 'green', 'blue', 'yellow']

    if st.session_state.tab_step[4] == 0 :
        if st.button('initialisation', key = 'init4') : 
            stroop_df = read_sheet('game4s')
            names = stroop_df['NAME']
            initialisation_game({"names" : names, "colors" : stroop_df['COLOR'], "type_click_4" : [None for _ in range (len(names))], 
                                    "delay_4" : [None for _ in range (len(names))]})
            st.session_state.tab_step[4] = 1 
            st.rerun()
        
    elif st.session_state.tab_step[4] == 1 : 

        if st.button("Start", key = 'st4'):

            initialisation_game({"start_time_color" : time.time(), "color_index" : 0})
            st.session_state.tab_step[4] = 2 
            st.rerun()

    elif st.session_state.tab_step[4] == 2 :
        names = st.session_state.names
        colors = st.session_state.colors

        count = st_autorefresh(interval=100, limit=int(10*dt*len(names)+5), key="refresher4")
        elapsed = time.time() - st.session_state.start_time_color
        st.session_state.color_index = int(elapsed // dt)

        if st.session_state.color_index < len(names):
            word = names[st.session_state.color_index]
            color = colors[st.session_state.color_index]
            st.write(f':{color}[{word}]')             

            for color_option in list_colors : 
                st.button(color_option, on_click = save_click, args = [4, color_option, st.session_state.color_index])

        else:
            success = [1 if st.session_state['type_click_4'][k] == names[k] else 0 for k in range (len(names))]
            rts = st.session_state['delay_4']

            if st.button('submit results') : 
                color_df = read_sheet('game4s')
                color_df[st.session_state.user] = success         
                color_df = write_sheet('game4s', color_df)

                color_df = read_sheet('game4t')
                color_df[st.session_state.user] = rts         
                color_df = write_sheet('game4t', color_df)

                st.session_state.tab_step[4] = 3
                st.rerun()
        
    else : 
        over('game 4')
        
    restart(4)





with time_aware : 

    initialisation_game({"time_stop_click" : None})

    
    def stop_click() : 
        delta = time.time() - st.session_state.start_time_guess
        st.session_state.time_stop_click = delta
        st.session_state.tab_step[5] = 2


    if st.session_state.tab_step[5] == 0  :

        if st.button("Start", key = 'st5'):
            st.session_state.start_time_guess = time.time()
            st.session_state.tab_step[5] = 1
            st.rerun()

    elif st.session_state.tab_step[5] == 1 : 
        st.button('STOP', on_click = stop_click)
    

    elif st.session_state.tab_step[5] == 2: 

        st.write(f'{int(st.session_state.time_stop_click)} seconds have passed')

        if st.button('submit results') : 
            time_df = read_sheet('game5')
            time_df[st.session_state.user] = st.session_state.time_stop_click         
            time_df = write_sheet('game5', time_df)

            st.session_state.tab_step[5] = 3
            st.rerun()

    else : 
        over('game 5')
        
    restart(5)
   

            
            