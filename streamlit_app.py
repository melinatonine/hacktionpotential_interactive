
from cProfile import label

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from random import randint 
import numpy as np 

st.title("Interactive session - homepage")

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

if 'language' not in st.session_state : 
    st.session_state.language = 'english'

game_name = ['Word list', 'Attention', 'Stroop', 'Time'] if st.session_state.language == 'english' else ['Liste de mots', 'Attention', 'Stroop', 'Temps']

if 'user' not in st.session_state:
    st.session_state.user = randint(0,1000)
    st.session_state.tab_step = [0 for _ in range (len(game_name)+1)]
    st.session_state.scores = [0 for _ in range (len(game_name))]
    st.session_state.trial =  0 


tabs = ["Registration"] + game_name + ["score"] if st.session_state.language == 'english' else ["Inscription"] + game_name +  ["résultats"]
login, word_game, attention, stroop, time_aware, score = st.tabs(tabs)



def initialisation_game(dict_state) : 
    for key in dict_state.keys() : 
        st.session_state[key] = dict_state[key] 
                        
#@st.cache_data
def read_sheet(sheet) : 
    return conn.read(worksheet = sheet)

#@st.cache_data
def write_sheet(sheet, df) : 
    return conn.update(data=df, worksheet = sheet) 


def save_click(game, label, position) : 
    if st.session_state[f"type_click_{game}"][position] is None : 
        st.session_state[f"type_click_{game}"][position] = label
        # get the delay since last letter shown
        st.session_state[f"delay_{game}"][position] = time.time() - st.session_state[f'start_time_{game}'] - dt*position

def restart(game, button = None) :

    if button is None :
        button = "Restart this part?" if st.session_state.language == 'english' else "Recommencer cette partie ?" 

    if st.button(button, key = f'{game}_{st.session_state.trial}') : 
        st.session_state.tab_step[game] = 0 
        st.session_state.trial += 1
        st.rerun()


def over(title = 'this part') : 
    st.write(f'You are done with {title} {st.session_state.user}' if st.session_state.language == 'english' else f'Vous avez terminé {title} {st.session_state.user}')


with login : 

    if st.session_state.tab_step[0] == 0 : 

        username = st.text_input('username', placeholder = 'firstname.surname (prénom.nom)', key = 'username')
        language = st.selectbox('language', ['english', 'français'])

        if st.button('OK', key = 'submitted0') : 
            user_df = read_sheet('users')
            # st.write(user_df)
            list_users = list(user_df['user-list'])
            if username in list_users : 

                st.write('Username already taken' if language == 'english' else 'Nom d\'utilisateur déjà pris')
            else : 
                user_df.loc[len(user_df.index)] = [username]
                user_df = write_sheet('users', user_df)
                st.session_state.user = username
                st.session_state.language = language
                st.session_state.tab_step[0] = 1
                st.rerun()

    else : 
        over('registration')
        restart(0, "Change username?" if st.session_state.language == 'english' else "Changer de nom d'utilisateur ?")
        

# GAME 1
with word_game : 

    dt = 1.5
    recall_delay = 5

    game = 0 

    @st.cache_data
    def listwords(words):
        word_list = ''
        for word in words : 
            word_list += f' {word}'

        st.write(word_list)

    st.write('In this part, you will need to memorize and recite a list of words.' if st.session_state.language == 'english'
              else 'Dans cette partie, vous devrez mémoriser puis réciter une liste de mots.')
    
    if st.session_state.tab_step[game+1] == 0 : 

        initialisation_game({'words' : []})
        word_df = read_sheet('game1')
        st.session_state.true_words = list(word_df['WORD']) if st.session_state.language == 'english' else list(word_df['MOT'])

        st.write('You will be shown a list of words, one at a time. Try to memorise them!' if st.session_state.language == 'english' else 'Vous allez voir une liste de mots, un à la fois. Essayez de les mémoriser !')
        
        if st.button('Start' if st.session_state.language == 'english' else 'Démarrer', key = 'st1') :
            st.session_state.start_time = time.time()
            st.session_state.word_index = 0
            st.session_state.tab_step[game+1] += 1
            st.rerun()
    
    elif st.session_state.tab_step[game+1] == 1 :

        twords = st.session_state.true_words
        count = st_autorefresh(interval=500, limit=int(10*dt*len(twords)+5), key="refresher")
        elapsed = time.time() - st.session_state.start_time
        st.session_state.word_index = int(elapsed // dt)

        if st.session_state.word_index < len(twords):
            word = twords[st.session_state.word_index]
            s = f"<p style='font-size:20px;'>{word}</p>"
            st.markdown(s, unsafe_allow_html=True)   

        elif elapsed < len(twords)*dt + recall_delay : 
            st.write('Get ready to recall the words!' if st.session_state.language == 'english' else 'Préparez-vous à réciter les mots !')
        else : 
            st.session_state.tab_step[game+1] += 1
            st.rerun()


    elif st.session_state.tab_step[game+1] == 2 : 

        with st.form('Words entry', clear_on_submit = True) : 
            w = st.text_input('Enter words here' if st.session_state.language == 'english' else 'Entrez les mots', value="", 
                              placeholder = 'word' if st.session_state.language == 'english' else 'mot', key='user_word')

            if st.form_submit_button('Add word to list' if st.session_state.language == 'english' else 'Ajouter le mot à la liste', key = 'submitted') :
                if w != "":
                    st.session_state.words.append(w)    
                    # st.session_state.user_word = ''  

            listwords(st.session_state.words)

        if st.button('Submit word list' if st.session_state.language == 'english' else 'Valider la liste de mots', key = 'submitted1') : 
            word_df = read_sheet('game1')
            score = 0
            words_user = list(set(st.session_state.words))
            for word in words_user : 
                mot = 'WORD' if st.session_state.language == 'english' else 'MOT'
                i = list(word_df.index[word_df[mot] == word])
                if len(i) == 1 : 
                    word_df.loc[i[0], 'COUNT'] += 1
                    score += 1
            word_df = write_sheet('game1', word_df)
            st.session_state.scores[game] = score
            st.session_state.tab_step[game+1] += 1
            st.rerun()
    
    else : 
        over(game_name[game])


with attention : 

    st.write('In this part, you will be shown a series of letters. For each letter, you will have to click on "Click if X" if you think the letter is an "X", and "Click if not X" if you think it is not an "X". Try to be as fast and accurate as possible!' if st.session_state.language == 'english'
             else 'Dans cette partie, vous allez voir une série de lettres. Pour chaque lettre, vous devrez cliquer sur "Click si X" si vous pensez que la lettre est un "X", et "Click si pas X" si vous pensez que ce n\'est pas un "X". Essayez d\'être aussi rapide et précis que possible !')

    dt = 2
    game = 1

    if st.session_state.tab_step[game+1] == 0 : 

        initialisation_game({"letter_count": 0})

        if st.button('initialisation', key = 'init3') : 
            
            attention_df = read_sheet('game3s')
            letters = attention_df['LETTER']
            initialisation_game({"letters" : letters, "type_click_3" : [None for _ in range (len(letters))], "delay_3" : [None for _ in range (len(letters))]})
            st.session_state.tab_step[game+1] = 1 
            st.rerun()

    elif st.session_state.tab_step[game+1] == 1 : 
        
        if st.button("Start", key = 'st3'):
            initialisation_game({"start_time_3" : time.time(), "letter_index" : 0})   
            st.session_state.tab_step[game+1] = 2 
            st.rerun()
    
    elif st.session_state.tab_step[game+1] == 2 :

        letters = st.session_state.letters
        count = st_autorefresh(interval=100, limit=int(10*dt*len(letters)+1), key="refresher")
        elapsed = time.time() - st.session_state.start_time_3
        st.session_state.letter_index = int(elapsed // dt)

        if st.session_state.letter_index < len(letters):
            letter = letters[st.session_state.letter_index]
            st.write(letter)             
            st.button("Click if X" if st.session_state.language == 'english' else "Cliquez si X", on_click = save_click, args = [3, "X", st.session_state.letter_index], key = 'clickx')
            st.button("Click if not X" if st.session_state.language == 'english' else "Cliquez si pas X", on_click = save_click, args = [3, "not_X", st.session_state.letter_index],  key = 'clicknotx')

        else:
            success = [1 if (letters[k] == "X" and st.session_state['type_click_3'][k] == "X") or (letters[k] != "X" and st.session_state['type_click_3'][k] == "not_X") else 0 for k in range (len(letters))]
            rts = st.session_state['delay_3']

            if st.button('submit results' if st.session_state.language == 'english' else 'Valider les résultats') : 
                attention_df = read_sheet('game3s')
                attention_df[st.session_state.user] = success         
                attention_df = write_sheet('game3s', attention_df)

                attention_df = read_sheet('game3t')
                attention_df[st.session_state.user] = rts         
                attention_df = write_sheet('game3t', attention_df)

                st.session_state.tab_step[game+1] = 3
                st.session_state.scores[game] = sum(success)/2
                st.rerun()
        
    else : 
        over(game_name[game])
        
        restart(game+1)



with stroop : 

    dt = 2.5
    game = 2

    list_colors = ['red', 'green', 'blue', 'pink', 'orange', 'black'] if st.session_state.language == 'english' else ['rouge', 'vert', 'bleu', 'rose', 'orange', 'noir']

    st.write('In this part, read the word (not the color of the writing) and click sur designated color. Try to be as fast and accurate as possible!' if st.session_state.language == 'english'
             else 'Dans cette partie, lisez le mot (et non la couleur de l\'écriture) et cliquez sur la couleur qu\'il désigne. Essayez d\'être aussi rapide et précis que possible !')
    
    st.write('Example: if you see  :green[red] , you should click on **red**.' if st.session_state.language == 'english' else 'Exemple : si vous voyez :green[rouge] , vous devez cliquer sur **rouge**.')
    
    if st.session_state.tab_step[game+1] == 0 :
        if st.button('initialisation', key = 'init4') : 
            stroop_df = read_sheet('game4s')
            names = stroop_df['NAME'] if st.session_state.language == 'english' else stroop_df['NOM']
            initialisation_game({"names" : names, "colors" : stroop_df['COLOR'], "type_click_4" : [None for _ in range (len(names))], 
                                    "delay_4" : [None for _ in range (len(names))]})
            st.session_state.tab_step[game+1] = 1 
            st.rerun()
        
    elif st.session_state.tab_step[game+1] == 1 : 

        if st.button("Press when you are ready!" if st.session_state.language == 'english' else "Clique ici pour commencer !", key = 'st4'):

            initialisation_game({"start_time_4" : time.time(), "color_index" : 0})
            st.session_state.tab_step[game+1] = 2 
            st.rerun()

    elif st.session_state.tab_step[game+1] == 2 :
        names = st.session_state.names
        colors = st.session_state.colors

        count = st_autorefresh(interval=100, limit=int(10*dt*len(names)+5), key="refresher4")
        elapsed = time.time() - st.session_state.start_time_4
        st.session_state.color_index = int(elapsed // dt)

        if st.session_state.color_index < len(names):
            word = names[st.session_state.color_index]
            color = colors[st.session_state.color_index]
            
            s = f"<p style='font-size:20px;color:{color};'>{word}</p>"
            st.markdown(s, unsafe_allow_html=True)   
      

            for color_option in list_colors : 
                st.button(f'**{color_option}**', on_click = save_click, args = [4, color_option, st.session_state.color_index])

        else:
            success = [1 if st.session_state['type_click_4'][k] == names[k] else 0 for k in range (len(names))]
            rts = st.session_state['delay_4']

            if st.button('submit results' if st.session_state.language == 'english' else 'Valider résultats') : 
                color_df = read_sheet('game4s')
                color_df[st.session_state.user] = success         
                color_df = write_sheet('game4s', color_df)

                color_df = read_sheet('game4t')
                color_df[st.session_state.user] = rts         
                color_df = write_sheet('game4t', color_df)

                st.session_state.tab_step[game+1] = 3
                st.session_state.scores[game] = sum(success)
                st.rerun()
        
    else : 
        over(game_name[game])
        
        restart(game+1)





with time_aware : 

    st.write('In this part, you will have to estimate when 30 seconds have passed. Try to be as accurate as possible!' if st.session_state.language == 'english' else 'Dans cette partie, vous devrez estimer quand 30 secondes se sont écoulées. Essayez d\'être aussi précis que possible !')
    st.write('Click on "Start" to start the timer, and then click on "Stop" when you think 30 seconds have passed.' if st.session_state.language == 'english' else 'Cliquez sur "Démarrer" pour lancer le chronomètre, puis cliquez sur "Stop" lorsque vous pensez que 30 secondes se sont écoulées.')

    game = 3
    
    def stop_click() : 
        delta = time.time() - st.session_state.start_time_guess
        st.session_state.time_stop_click = delta
        st.session_state.tab_step[game+1] = 2


    if st.session_state.tab_step[game+1] == 0  :

        initialisation_game({"time_stop_click" : 0})
        if st.button("Start" if st.session_state.language == 'english' else "Démarrer", key = 'st5'):
            st.session_state.start_time_guess = time.time()
            st.session_state.tab_step[game+1] = 1
            st.rerun()

    elif st.session_state.tab_step[game+1] == 1 : 
        st.button('STOP', on_click = stop_click)
    

    elif st.session_state.tab_step[game+1] == 2: 

        st.write(f'{int(st.session_state.time_stop_click)} seconds have passed' if st.session_state.language == 'english' else f'{int(st.session_state.time_stop_click)} secondes se sont écoulées')

        if st.button('submit results' if st.session_state.language == 'english' else 'Valider résultats') : 
            time_df = read_sheet('game5')
            time_df[st.session_state.user] = st.session_state.time_stop_click         
            time_df = write_sheet('game5', time_df)

            st.session_state.scores[game] = 20 - abs(st.session_state.time_stop_click - 30)
            st.session_state.tab_step[game+1] = 3
            st.rerun()

    else : 
        over(game_name[game])
        
        restart(game+1)
   

            
with score :

    st.write('In this part, you can see your results!' if st.session_state.language == 'english' else 'Dans cette partie, vous pouvez voir vos résultats!')

    for i in range (len(game_name)) :
        st.write(f'Your score for game {game_name[i]} is : {int(st.session_state.scores[i])}/20' if st.session_state.language == 'english' else f'Votre score pour le jeu {game_name[i]} est : {int(st.session_state.scores[i])}/20')
    
    if st.button('Send scores' if st.session_state.language == 'english' else 'Envoyer les scores', key = 'submit_final_score') : 
        score_df = read_sheet('scores')
        score_df[st.session_state.user] = st.session_state.scores         
        score_df = write_sheet('scores', score_df)
        st.write('Scores sent! Thank you for participating!' if st.session_state.language == 'english' else 'Scores envoyés! Merci pour votre participation !')
