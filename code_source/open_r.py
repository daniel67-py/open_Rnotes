#!/usr/bin/python3
#-*- coding: utf-8 -*-
import os
import sys
import ssl
import smtplib
import sqlite3
import configparser
from datetime import *
from tkinter import *
from tkinter.messagebox import *
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

####################################################################################################
### Open_Rnotes version 0.1 - application paramétrable de saisie simplifié
### développé par Meyer Daniel sous Python 3.8 pour Linux et Windows
### programme sous license MIT  -  mars 2021
####################################################################################################

class Open_Rnotes(Tk):
    def __init__(self):
        # définition de la fenetre principale
        Tk.__init__(self)
        self.title('Open_Rnotes')
        self.resizable(width = False, height = False)

        # lecture du fichier de configuration
        self.config = configparser.ConfigParser()
        self.config.read('open_r.ini')
        # compte du nombre de sections dans le fichier de configuration
        n = len(self.config.sections())
        # récupération du nom des sections dans une liste
        s = self.config.sections()

        # mise en place des champs de saisies définis par le fichier de configuration

        for x in range(0, n):
            Label(self, text = self.config[s[x]].get('lib')).grid(row = x, column = 1)
            if s[x].startswith('ZONE') and self.config[s[x]].get('type') == 'champ':
                # définition du widget 
                self.conteneur = Entry(self, width = 15)
                self.conteneur.insert('0', 'à renseigner')
                self.conteneur.grid(row = x, column = 2)
                # création d'une variable portant le nom de la section lu du fichier de config
                # et relié à la zone de saisie correspondante
                globals()[self.config[s[x]].get('lib')] = self.conteneur
            elif s[x].startswith('ZONE') and self.config[s[x]].get('type') == 'choix':
                # récupération de la liste des options possible
                liste_options = self.config[s[x]].get('chx')
                liste_options = liste_options.split()
                # création d'une stringvar pour définir le choix dans le widget
                self.pointer = StringVar()
                self.pointer.set(liste_options[0])
                # définition du widget
                self.menu = OptionMenu(self, self.pointer, *liste_options)
                self.menu.grid(row = x, column = 2)
                # même opération que pour une zone de texte, mais en intégrant le menu dans une variable
                globals()[self.config[s[x]].get('lib')] = self.pointer

        # boutons d'actions
        quitter = Button(self, text = "Quitter", width = 15, command = self.fin_session)
        quitter.grid(row = 100, column = 1)
        saisir = Button(self, text = "Saisir", width = 15, command = self.saisir)
        saisir.grid(row = 100, column = 2)

        # bouclage de la fenetre
        self.mainloop()
        # gestion propre de la fermeture de l'application
        try:
            self.destroy()
        except TclError:
            sys.exit()

    ################################################################################################
    ### fonction de fermeture de l'application
    ################################################################################################
    def fin_session(self):
        question = askyesno('Finir ?', 'Voulez vous quitter le programme ?')
        if question == True:
            exit()
            
    ################################################################################################
    ### fonction de saisie
    ################################################################################################
    def saisir(self):
        # récupération de la liste des sections dans le fichier config
        l = self.config.sections()
        # compte du nombre de sections dans le fichier de configuration
        n = len(self.config.sections())
        # préparation d'une ligne vide pour l'ajout dans le fichier
        ligne = ""

        # récupération des noms des variables contenant les zones de saisies
        # et du contenu des widgets concernés
        for x in range(0, n):
            if l[x].startswith('ZONE'):
                variable = globals()[self.config[l[x]].get('lib')]
                ligne = ligne + variable.get() + ", "

        # récupération de la date et de l'heure
        moment = datetime.now()
        datum = moment.strftime(" %d / %m / %Y ,")
        heure = moment.strftime(" %H : %M : %S ,")

        # premier cas, sortie dans un fichier texte
        if self.config['PARAMS'].get('out_type') == 'txt':
            with open(self.config['PARAMS'].get('text_out_file'), 'a') as fichier:
                fichier.write(datum + heure + ligne + "\n")
            self.ok_saisie()

        # second cas, sortie dans un fichier csv
        elif self.config['PARAMS'].get('out_type') == 'csv':
            en_tete = "date, heure, "
            if os.path.exists(self.config['PARAMS'].get('csv_out_file')) == False:
                with open(self.config['PARAMS'].get('csv_out_file'), 'a') as fichier:
                    for x in range(0, n):
                        if l[x].startswith('ZONE'):
                            en_tete = en_tete + self.config[l[x]].get('lib') + ", "
                    fichier.write(en_tete + "\n")
                    fichier.write(datum + heure + ligne + "\n")
            elif os.path.exists(self.config['PARAMS'].get('csv_out_file')) == True:
                with open(self.config['PARAMS'].get('csv_out_file'), 'a') as fichier:
                    fichier.write(datum + heure + ligne + "\n")
            self.ok_saisie()

        # sinon
        else:
            self.probleme_saisie()

        # et pour finir, envoi d'un mail le cas échéant
        if self.config['PARAMS'].get('signal') == 'oui':
            text_html = f"""
<p> Email automatique d'une application Open_Rnotes déployée vous concernant.
<br> le : {datum}
<br> à  : {heure}
<br> <hr> <br> {ligne} <br>
<br> <hr> <br> fin de transmission
</p>"""
            self.envoi_mail(text_html)

    ################################################################################################
    ### fonction signalant à l'utilisateur que la saisie a été faite
    ################################################################################################
    def ok_saisie(self):
        showinfo('okay !', 'la saisie a bien été prise en compte')

    ################################################################################################
    ### fonction signalant à l'utilisateur qu'il y a un problème
    ################################################################################################
    def probleme_saisie(self):
        showerror('heum...', 'type de sortie de fichier non valable')

    ################################################################################################
    ### fonction permettant d'envoyer un mail si l'utilisateur le souhaite
    ################################################################################################
    def envoi_mail(self, text):
        smtp_adress = self.config['PARAMS'].get('servor')
        smtp_port = 465
        email_adress = self.config['PARAMS'].get('adress')
        email_password = self.config['PARAMS'].get('passwd')
        email_receiver = self.config['PARAMS'].get('send_to')

        message = MIMEMultipart("alternative")
        message["Subject"] = self.config['PARAMS'].get('mail_obj')
        message["From"] = email_adress
        message["To"] = email_receiver

        text = "<p>" + text + "</p>"

        html_mime = MIMEText(text, 'html')
        
        message.attach(html_mime)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_adress, smtp_port, context = context) as server:
            server.login(email_adress, email_password)
            server.sendmail(email_adress, email_receiver, message.as_string())
            showinfo('okay !', 'le relevé a été envoyé')
                        
####################################################################################################
### lancement de l'application
####################################################################################################
run_me = Open_Rnotes()
run_me
