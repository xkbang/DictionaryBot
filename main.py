import customtkinter as ctk
from UI import DictionaryApp
from Chatbot import chatbot

if __name__ == "__main__":
    my_chatbot = chatbot()
    root = ctk.CTk()
    app = DictionaryApp(root, my_chatbot)
    root.mainloop()