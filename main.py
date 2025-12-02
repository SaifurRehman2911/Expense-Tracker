from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.window import Window
from datetime import datetime, timedelta
import json
import hashlib
import os
from collections import defaultdict

Window.clearcolor = (0.95, 0.95, 0.97, 1)

# Secure data storage with encryption
class SecureStorage:
    def __init__(self, filename='main_data.json'):
        self.filename = filename
        self.password_hash = None
        self.load_password()
    
    def load_password(self):
        if os.path.exists('auth.dat'):
            with open('auth.dat', 'r') as f:
                self.password_hash = f.read()
    
    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        with open('auth.dat', 'w') as f:
            f.write(self.password_hash)
    
    def verify_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
    
    def save_data(self, data):
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return {'expenses': [], 'income': [], 'loans': []}

# Login Screen
class LoginScreen(Screen):
    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        title = Label(text='[b]Expense Tracker[/b]', font_size='32sp', 
                     size_hint=(1, 0.3), markup=True, color=(0.2, 0.4, 0.8, 1))
        
        input_area = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.4))
        
        self.password_input = TextInput(hint_text='Enter Password', 
                                       password=True, multiline=False,
                                       size_hint=(1, None), height=50)
        
        login_btn = Button(text='Login', size_hint=(1, None), height=50,
                          background_color=(0.2, 0.6, 1, 1))
        login_btn.bind(on_press=self.login)
        
        setup_btn = Button(text='Setup Password (First Time)', 
                          size_hint=(1, None), height=50,
                          background_color=(0.3, 0.7, 0.3, 1))
        setup_btn.bind(on_press=self.setup_password)
        
        input_area.add_widget(Label(text='', size_hint=(1, 0.2)))
        input_area.add_widget(self.password_input)
        input_area.add_widget(login_btn)
        input_area.add_widget(setup_btn)
        input_area.add_widget(Label(text='', size_hint=(1, 0.2)))
        
        layout.add_widget(title)
        layout.add_widget(input_area)
        layout.add_widget(Label(text='', size_hint=(1, 0.3)))
        
        self.add_widget(layout)
    
    def login(self, instance):
        password = self.password_input.text
        if self.storage.password_hash and self.storage.verify_password(password):
            self.manager.current = 'dashboard'
            self.password_input.text = ''
        else:
            self.show_popup('Error', 'Invalid password!')
    
    def setup_password(self, instance):
        password = self.password_input.text
        if len(password) < 4:
            self.show_popup('Error', 'Password must be at least 4 characters!')
            return
        self.storage.set_password(password)
        self.show_popup('Success', 'Password set successfully! Please login.')
        self.password_input.text = ''
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                     size_hint=(0.7, 0.3))
        popup.open()

# Dashboard Screen
class DashboardScreen(Screen):
    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.build_ui()
    
    def build_ui(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = BoxLayout(size_hint=(1, 0.1), spacing=10)
        title = Label(text='[b]Dashboard[/b]', font_size='24sp', markup=True)
        logout_btn = Button(text='Logout', size_hint=(0.2, 1),
                           background_color=(0.8, 0.3, 0.3, 1))
        logout_btn.bind(on_press=self.logout)
        header.add_widget(title)
        header.add_widget(logout_btn)
        
        data = self.storage.load_data()
        total_income = sum(item['amount'] for item in data['income'])
        total_expense = sum(item['amount'] for item in data['expenses'])
        loans_given = sum(item['amount'] for item in data['loans'] if item['type'] == 'given')
        loans_taken = sum(item['amount'] for item in data['loans'] if item['type'] == 'taken')
        balance = total_income - total_expense
        
        summary = GridLayout(cols=2, size_hint=(1, 0.25), spacing=10)
        summary.add_widget(self.create_card('Income', f'Rs. {total_income:,.2f}', (0.3, 0.7, 0.3, 1)))
        summary.add_widget(self.create_card('Expenses', f'Rs. {total_expense:,.2f}', (0.8, 0.3, 0.3, 1)))
        summary.add_widget(self.create_card('Balance', f'Rs. {balance:,.2f}', (0.2, 0.5, 0.8, 1)))
        summary.add_widget(self.create_card('Loans Net', f'Rs. {loans_given - loans_taken:,.2f}', (0.9, 0.6, 0.2, 1)))
        
        nav = GridLayout(cols=2, size_hint=(1, 0.35), spacing=10)
        
        buttons = [
            ('Add Expense', 'add_expense', (0.8, 0.3, 0.3, 1)),
            ('Add Income', 'add_income', (0.3, 0.7, 0.3, 1)),
            ('Manage Loans', 'loans', (0.9, 0.6, 0.2, 1)),
            ('View Reports', 'reports', (0.5, 0.3, 0.8, 1)),
            ('Search & Filter', 'search', (0.2, 0.6, 0.8, 1)),
            ('Budget Planner', 'budget', (0.3, 0.5, 0.7, 1))
        ]
        
        for text, screen, color in buttons:
            btn = Button(text=text, background_color=color)
            btn.bind(on_press=lambda x, s=screen: self.navigate(s))
            nav.add_widget(btn)
        
        layout.add_widget(header)
        layout.add_widget(summary)
        layout.add_widget(nav)
        
        self.add_widget(layout)
    
    def create_card(self, title, value, color):
        card = BoxLayout(orientation='vertical', padding=10)
        with card.canvas.before:
            Color(*color)
            card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
        card.bind(pos=lambda x, y: setattr(card.rect, 'pos', y),
                 size=lambda x, y: setattr(card.rect, 'size', y))
        
        card.add_widget(Label(text=title, font_size='14sp', bold=True))
        card.add_widget(Label(text=value, font_size='24sp', bold=True))
        return card
    
    def navigate(self, screen_name):
        if screen_name in self.manager.screen_names:
            screen = self.manager.get_screen(screen_name)
            if hasattr(screen, 'refresh'):
                screen.refresh()
            self.manager.current = screen_name
    
    def logout(self, instance):
        self.manager.current = 'login'
    
    def on_enter(self):
        self.build_ui()

# Add Expense Screen
class AddExpenseScreen(Screen):
    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        header = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(text='← Back', size_hint=(0.2, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        title = Label(text='[b]Add Expense[/b]', font_size='20sp', markup=True)
        header.add_widget(back_btn)
        header.add_widget(title)
        
        form = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.8))
        
        self.amount_input = TextInput(hint_text='Amount', multiline=False, 
                                      input_filter='float', height=40, size_hint=(1, None))
        self.description_input = TextInput(hint_text='Description', height=40, 
                                          size_hint=(1, None))
        self.category_spinner = Spinner(text='Select Category',
                                       values=['Food', 'Transport', 'Shopping', 
                                              'Bills', 'Entertainment', 'Health', 
                                              'Education', 'Other'],
                                       height=40, size_hint=(1, None))
        self.payment_spinner = Spinner(text='Payment Method',
                                      values=['Cash', 'Card', 'UPI', 'Bank Transfer'],
                                      height=40, size_hint=(1, None))
        
        recurring = BoxLayout(size_hint=(1, None), height=40)
        recurring.add_widget(Label(text='Recurring:', size_hint=(0.3, 1)))
        self.recurring_spinner = Spinner(text='No',
                                        values=['No', 'Daily', 'Weekly', 'Monthly'],
                                        size_hint=(0.7, 1))
        recurring.add_widget(self.recurring_spinner)
        
        add_btn = Button(text='Add Expense', size_hint=(1, None), height=50,
                        background_color=(0.8, 0.3, 0.3, 1))
        add_btn.bind(on_press=self.add_expense)
        
        form.add_widget(Label(text=''))
        form.add_widget(self.amount_input)
        form.add_widget(self.description_input)
        form.add_widget(self.category_spinner)
        form.add_widget(self.payment_spinner)
        form.add_widget(recurring)
        form.add_widget(add_btn)
        form.add_widget(Label(text=''))
        
        layout.add_widget(header)
        layout.add_widget(form)
        
        self.add_widget(layout)
    
    def add_expense(self, instance):
        try:
            amount = float(self.amount_input.text)
            description = self.description_input.text
            category = self.category_spinner.text
            payment = self.payment_spinner.text
            recurring = self.recurring_spinner.text
            
            if category == 'Select Category' or payment == 'Payment Method':
                self.show_popup('Error', 'Please fill all fields!')
                return
            
            data = self.storage.load_data()
            expense = {
                'amount': amount,
                'description': description,
                'category': category,
                'payment_method': payment,
                'recurring': recurring,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'id': len(data['expenses']) + 1
            }
            data['expenses'].append(expense)
            self.storage.save_data(data)
            
            self.show_popup('Success', 'Expense added successfully!')
            self.clear_form()
        except ValueError:
            self.show_popup('Error', 'Please enter a valid amount!')
    
    def clear_form(self):
        self.amount_input.text = ''
        self.description_input.text = ''
        self.category_spinner.text = 'Select Category'
        self.payment_spinner.text = 'Payment Method'
        self.recurring_spinner.text = 'No'
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                     size_hint=(0.7, 0.3))
        popup.open()

# Add Income Screen
class AddIncomeScreen(Screen):
    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        header = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(text='← Back', size_hint=(0.2, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        title = Label(text='[b]Add Income[/b]', font_size='20sp', markup=True)
        header.add_widget(back_btn)
        header.add_widget(title)
        
        form = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.8))
        
        self.amount_input = TextInput(hint_text='Amount', multiline=False,
                                      input_filter='float', height=40, size_hint=(1, None))
        self.description_input = TextInput(hint_text='Description', height=40,
                                          size_hint=(1, None))
        self.source_spinner = Spinner(text='Income Source',
                                     values=['Salary', 'Freelance', 'Investment',
                                            'Gift', 'Loan Returned', 'Business', 'Other'],
                                     height=40, size_hint=(1, None))
        
        recurring = BoxLayout(size_hint=(1, None), height=40)
        recurring.add_widget(Label(text='Recurring:', size_hint=(0.3, 1)))
        self.recurring_spinner = Spinner(text='No',
                                        values=['No', 'Weekly', 'Monthly', 'Yearly'],
                                        size_hint=(0.7, 1))
        recurring.add_widget(self.recurring_spinner)
        
        add_btn = Button(text='Add Income', size_hint=(1, None), height=50,
                        background_color=(0.3, 0.7, 0.3, 1))
        add_btn.bind(on_press=self.add_income)
        
        form.add_widget(Label(text=''))
        form.add_widget(self.amount_input)
        form.add_widget(self.description_input)
        form.add_widget(self.source_spinner)
        form.add_widget(recurring)
        form.add_widget(add_btn)
        form.add_widget(Label(text=''))
        
        layout.add_widget(header)
        layout.add_widget(form)
        
        self.add_widget(layout)
    
    def add_income(self, instance):
        try:
            amount = float(self.amount_input.text)
            description = self.description_input.text
            source = self.source_spinner.text
            recurring = self.recurring_spinner.text
            
            if source == 'Income Source':
                self.show_popup('Error', 'Please select income source!')
                return
            
            data = self.storage.load_data()
            income = {
                'amount': amount,
                'description': description,
                'source': source,
                'recurring': recurring,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'id': len(data['income']) + 1
            }
            data['income'].append(income)
            self.storage.save_data(data)
            
            self.show_popup('Success', 'Income added successfully!')
            self.clear_form()
        except ValueError:
            self.show_popup('Error', 'Please enter a valid amount!')
    
    def clear_form(self):
        self.amount_input.text = ''
        self.description_input.text = ''
        self.source_spinner.text = 'Income Source'
        self.recurring_spinner.text = 'No'
    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                     size_hint=(0.7, 0.3))
        popup.open()

# Loans Screen
class LoansScreen(Screen):
    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.build_ui()
    
    def build_ui(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(text='← Back', size_hint=(0.15, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        title = Label(text='[b]Loan Management[/b]', font_size='20sp', markup=True)
        add_btn = Button(text='+ Add Loan', size_hint=(0.25, 1),
                        background_color=(0.2, 0.6, 1, 1))
        add_btn.bind(on_press=self.show_add_popup)
        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(add_btn)
        
        tabs = BoxLayout(size_hint=(1, 0.08), spacing=5)
        given_btn = Button(text='Given', background_color=(0.3, 0.7, 0.3, 1))
        taken_btn = Button(text='Taken', background_color=(0.8, 0.3, 0.3, 1))
        given_btn.bind(on_press=lambda x: self.show_loans('given'))
        taken_btn.bind(on_press=lambda x: self.show_loans('taken'))
        tabs.add_widget(given_btn)
        tabs.add_widget(taken_btn)
        
        self.loan_scroll = ScrollView(size_hint=(1, 0.82))
        self.loan_list = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.loan_list.bind(minimum_height=self.loan_list.setter('height'))
        self.loan_scroll.add_widget(self.loan_list)
        
        layout.add_widget(header)
        layout.add_widget(tabs)
        layout.add_widget(self.loan_scroll)
        
        self.add_widget(layout)
        self.show_loans('given')
    
    def show_loans(self, loan_type):
        self.loan_list.clear_widgets()
        data = self.storage.load_data()
        loans = [l for l in data['loans'] if l['type'] == loan_type and l.get('status', 'active') == 'active']
        
        if not loans:
            self.loan_list.add_widget(Label(text=f'No {loan_type} loans', size_hint_y=None, height=50))
            return
        
        for loan in loans:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=100, padding=10, spacing=5)
            with card.canvas.before:
                color = (0.3, 0.7, 0.3, 0.3) if loan_type == 'given' else (0.8, 0.3, 0.3, 0.3)
                Color(*color)
                card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[5])
            card.bind(pos=lambda x, y: setattr(x.rect, 'pos', y),
                     size=lambda x, y: setattr(x.rect, 'size', y))
            
            info = BoxLayout(orientation='vertical')
            info.add_widget(Label(text=f"[b]{loan['person']}[/b] - Rs. {loan['amount']:,.2f}", 
                                 markup=True, size_hint_y=0.4))
            info.add_widget(Label(text=f"{loan['description']} | Due: {loan.get('due_date', 'N/A')}", 
                                 font_size='12sp', size_hint_y=0.3))
            
            settle_btn = Button(text='Settle', size_hint=(None, 0.3), width=80)
            settle_btn.bind(on_press=lambda x, l=loan: self.settle_loan(l))
            
            bottom = BoxLayout(size_hint_y=0.3)
            bottom.add_widget(Label(text=loan['date'][:10], font_size='11sp'))
            bottom.add_widget(settle_btn)
            
            card.add_widget(info)
            card.add_widget(bottom)
            self.loan_list.add_widget(card)
    
    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        amount_input = TextInput(hint_text='Amount', input_filter='float', multiline=False)
        person_input = TextInput(hint_text='Person Name', multiline=False)
        desc_input = TextInput(hint_text='Description', multiline=False)
        type_spinner = Spinner(text='Loan Type', values=['given', 'taken'])
        due_input = TextInput(hint_text='Due Date (YYYY-MM-DD)', multiline=False)
        
        content.add_widget(amount_input)
        content.add_widget(person_input)
        content.add_widget(desc_input)
        content.add_widget(type_spinner)
        content.add_widget(due_input)
        
        add_btn = Button(text='Add Loan', size_hint=(1, None), height=40)
        content.add_widget(add_btn)
        
        popup = Popup(title='Add Loan', content=content, size_hint=(0.8, 0.6))
        
        def add_loan(x):
            try:
                data = self.storage.load_data()
                loan = {
                    'amount': float(amount_input.text),
                    'person': person_input.text,
                    'description': desc_input.text,
                    'type': type_spinner.text,
                    'due_date': due_input.text,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'active',
                    'id': len(data['loans']) + 1
                }
                data['loans'].append(loan)
                self.storage.save_data(data)
                popup.dismiss()
                self.refresh()
            except:
                pass
        
        add_btn.bind(on_press=add_loan)
        popup.open()
    
    def settle_loan(self, loan):
        data = self.storage.load_data()
        for l in data['loans']:
            if l['id'] == loan['id']:
                l['status'] = 'settled'
                l['settled_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.storage.save_data(data)
        self.refresh()
    
    def refresh(self):
        self.build_ui()

# Search and Filter Screen
class SearchScreen(Screen):
    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(text='← Back', size_hint=(0.2, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        title = Label(text='[b]Search & Filter[/b]', font_size='20sp', markup=True)
        header.add_widget(back_btn)
        header.add_widget(title)
        
        search_box = BoxLayout(orientation='vertical', size_hint=(1, 0.2), spacing=5)
        self.search_input = TextInput(hint_text='Search by description...', 
                                     size_hint=(1, None), height=40)
        
        filters = BoxLayout(size_hint=(1, None), height=40, spacing=5)
        self.type_filter = Spinner(text='All', values=['All', 'Expenses', 'Income'])
        self.category_filter = Spinner(text='All Categories',
                                      values=['All Categories', 'Food', 'Transport', 
                                             'Shopping', 'Bills', 'Entertainment', 
                                             'Health', 'Education', 'Other'])
        filters.add_widget(self.type_filter)
        filters.add_widget(self.category_filter)
        
        search_btn = Button(text='Search', size_hint=(1, None), height=40,
                          background_color=(0.2, 0.6, 1, 1))
        search_btn.bind(on_press=self.perform_search)
        
        search_box.add_widget(self.search_input)
        search_box.add_widget(filters)
        search_box.add_widget(search_btn)
        
        self.results_scroll = ScrollView(size_hint=(1, 0.7))
        self.results_list = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.results_list.bind(minimum_height=self.results_list.setter('height'))
        self.results_scroll.add_widget(self.results_list)
        
        layout.add_widget(header)
        layout.add_widget(search_box)
        layout.add_widget(self.results_scroll)
        
        self.add_widget(layout)
    
    def perform_search(self, instance):
        self.results_list.clear_widgets()
        data = self.storage.load_data()
        search_term = self.search_input.text.lower()
        type_filter = self.type_filter.text
        category_filter = self.category_filter.text
        
        results = []
        
        if type_filter in ['All', 'Expenses']:
            for exp in data['expenses']:
                if (search_term in exp['description'].lower() and
                    (category_filter == 'All Categories' or exp['category'] == category_filter)):
                    results.append(('Expense', exp))
        
        if type_filter in ['All', 'Income']:
            for inc in data['income']:
                if search_term in inc['description'].lower():
                    results.append(('Income', inc))
        
        if not results:
            self.results_list.add_widget(Label(text='No results found', 
                                              size_hint_y=None, height=50))
            return
        
        for item_type, item in results:
            card = BoxLayout(orientation='vertical', size_hint_y=None, 
                           height=80, padding=8, spacing=3)
            
            color = (0.8, 0.3, 0.3, 0.2) if item_type == 'Expense' else (0.3, 0.7, 0.3, 0.2)
            with card.canvas.before:
                Color(*color)
                card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[5])
            card.bind(pos=lambda x, y: setattr(x.rect, 'pos', y),
                     size=lambda x, y: setattr(x.rect, 'size', y))
            
            title_text = f"[b]{item_type}[/b] - Rs. {item['amount']:,.2f}"
            if item_type == 'Expense':
                title_text += f" ({item['category']})"
            
            card.add_widget(Label(text=title_text, markup=True, size_hint_y=0.4))
            card.add_widget(Label(text=item['description'], font_size='12sp', 
                                 size_hint_y=0.3))
            card.add_widget(Label(text=item['date'][:10], font_size='11sp', 
                                 size_hint_y=0.3))
            
            self.results_list.add_widget(card)

# Reports Screen
class ReportsScreen(Screen):
    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.build_ui()
    
    def build_ui(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(text='← Back', size_hint=(0.2, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        title = Label(text='[b]Financial Reports[/b]', font_size='20sp', markup=True)
        header.add_widget(back_btn)
        header.add_widget(title)
        
        period_box = BoxLayout(size_hint=(1, 0.08), spacing=5)
        periods = ['This Week', 'This Month', 'Last Month', 'This Year', 'All Time']
        for period in periods:
            btn = Button(text=period, background_color=(0.3, 0.5, 0.7, 1))
            btn.bind(on_press=lambda x, p=period: self.generate_report(p))
            period_box.add_widget(btn)
        
        self.report_scroll = ScrollView(size_hint=(1, 0.82))
        self.report_content = BoxLayout(orientation='vertical', spacing=10, 
                                       size_hint_y=None, padding=10)
        self.report_content.bind(minimum_height=self.report_content.setter('height'))
        self.report_scroll.add_widget(self.report_content)
        
        layout.add_widget(header)
        layout.add_widget(period_box)
        layout.add_widget(self.report_scroll)
        
        self.add_widget(layout)
        self.generate_report('This Month')
    
    def generate_report(self, period):
        self.report_content.clear_widgets()
        data = self.storage.load_data()
        
        now = datetime.now()
        if period == 'This Week':
            start_date = now - timedelta(days=now.weekday())
        elif period == 'This Month':
            start_date = now.replace(day=1)
        elif period == 'Last Month':
            last_month = now.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1)
            now = now.replace(day=1)
        elif period == 'This Year':
            start_date = now.replace(month=1, day=1)
        else:
            start_date = datetime(2000, 1, 1)
        
        expenses = [e for e in data['expenses'] 
                   if datetime.strptime(e['date'], '%Y-%m-%d %H:%M:%S') >= start_date
                   and datetime.strptime(e['date'], '%Y-%m-%d %H:%M:%S') <= now]
        income = [i for i in data['income']
                 if datetime.strptime(i['date'], '%Y-%m-%d %H:%M:%S') >= start_date
                 and datetime.strptime(i['date'], '%Y-%m-%d %H:%M:%S') <= now]
        
        total_expense = sum(e['amount'] for e in expenses)
        total_income = sum(i['amount'] for i in income)
        balance = total_income - total_expense
        
        summary = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=10)
        with summary.canvas.before:
            Color(0.2, 0.5, 0.8, 0.3)
            summary.rect = RoundedRectangle(pos=summary.pos, size=summary.size, radius=[10])
        summary.bind(pos=lambda x, y: setattr(x.rect, 'pos', y),
                    size=lambda x, y: setattr(x.rect, 'size', y))
        
        summary.add_widget(Label(text=f'[b]{period} Summary[/b]', markup=True, 
                                font_size='18sp', size_hint_y=0.3))
        summary.add_widget(Label(text=f'Income: Rs. {total_income:,.2f} | Expenses: Rs. {total_expense:,.2f}',
                                font_size='14sp', size_hint_y=0.35))
        color_text = '[color=00ff00]' if balance >= 0 else '[color=ff0000]'
        summary.add_widget(Label(text=f'{color_text}Balance: Rs. {balance:,.2f}[/color]',
                                markup=True, font_size='16sp', size_hint_y=0.35))
        
        self.report_content.add_widget(summary)
        
        if expenses:
            cat_title = Label(text='[b]Expense by Category[/b]', markup=True,
                            font_size='16sp', size_hint_y=None, height=40)
            self.report_content.add_widget(cat_title)
            
            categories = defaultdict(float)
            for exp in expenses:
                categories[exp['category']] += exp['amount']
            
            for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                
                cat_card = BoxLayout(orientation='vertical', size_hint_y=None, 
                                    height=60, padding=8)
                with cat_card.canvas.before:
                    Color(0.9, 0.9, 0.9, 1)
                    cat_card.rect = RoundedRectangle(pos=cat_card.pos, 
                                                     size=cat_card.size, radius=[5])
                cat_card.bind(pos=lambda x, y: setattr(x.rect, 'pos', y),
                            size=lambda x, y: setattr(x.rect, 'size', y))
                
                cat_card.add_widget(Label(text=f'[b]{cat}[/b]', markup=True, 
                                         size_hint_y=0.5))
                cat_card.add_widget(Label(text=f'Rs. {amount:,.2f} ({percentage:.1f}%)',
                                         font_size='13sp', size_hint_y=0.5))
                
                self.report_content.add_widget(cat_card)
        
        if income:
            inc_title = Label(text='[b]Income by Source[/b]', markup=True,
                            font_size='16sp', size_hint_y=None, height=40)
            self.report_content.add_widget(inc_title)
            
            sources = defaultdict(float)
            for inc in income:
                sources[inc['source']] += inc['amount']
            
            for source, amount in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / total_income * 100) if total_income > 0 else 0
                
                src_card = BoxLayout(orientation='vertical', size_hint_y=None,
                                    height=60, padding=8)
                with src_card.canvas.before:
                    Color(0.9, 0.95, 0.9, 1)
                    src_card.rect = RoundedRectangle(pos=src_card.pos,
                                                     size=src_card.size, radius=[5])
                src_card.bind(pos=lambda x, y: setattr(x.rect, 'pos', y),
                            size=lambda x, y: setattr(x.rect, 'size', y))
                
                src_card.add_widget(Label(text=f'[b]{source}[/b]', markup=True,
                                         size_hint_y=0.5))
                src_card.add_widget(Label(text=f'Rs. {amount:,.2f} ({percentage:.1f}%)',
                                         font_size='13sp', size_hint_y=0.5))
                
                self.report_content.add_widget(src_card)
    
    def refresh(self):
        self.build_ui()

# Budget Planner Screen
class BudgetScreen(Screen):
    def __init__(self, storage, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.build_ui()
    
    def build_ui(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(text='← Back', size_hint=(0.2, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        title = Label(text='[b]Budget Planner[/b]', font_size='20sp', markup=True)
        add_btn = Button(text='+ Set Budget', size_hint=(0.25, 1),
                        background_color=(0.2, 0.6, 1, 1))
        add_btn.bind(on_press=self.show_budget_popup)
        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(add_btn)
        
        self.budget_scroll = ScrollView(size_hint=(1, 0.9))
        self.budget_list = BoxLayout(orientation='vertical', spacing=10,
                                     size_hint_y=None, padding=10)
        self.budget_list.bind(minimum_height=self.budget_list.setter('height'))
        self.budget_scroll.add_widget(self.budget_list)
        
        layout.add_widget(header)
        layout.add_widget(self.budget_scroll)
        
        self.add_widget(layout)
        self.load_budgets()
    
    def load_budgets(self):
        self.budget_list.clear_widgets()
        data = self.storage.load_data()
        
        if 'budgets' not in data:
            data['budgets'] = {}
        
        budgets = data.get('budgets', {})
        
        now = datetime.now()
        start_of_month = now.replace(day=1)
        expenses = [e for e in data['expenses']
                   if datetime.strptime(e['date'], '%Y-%m-%d %H:%M:%S') >= start_of_month]
        
        spending = defaultdict(float)
        for exp in expenses:
            spending[exp['category']] += exp['amount']
        
        categories = ['Food', 'Transport', 'Shopping', 'Bills', 
                     'Entertainment', 'Health', 'Education', 'Other']
        
        for category in categories:
            budget_amount = budgets.get(category, 0)
            spent = spending.get(category, 0)
            remaining = budget_amount - spent
            percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0
            
            card = BoxLayout(orientation='vertical', size_hint_y=None,
                           height=100, padding=10, spacing=5)
            
            if budget_amount == 0:
                color = (0.7, 0.7, 0.7, 0.3)
            elif percentage > 100:
                color = (0.9, 0.2, 0.2, 0.4)
            elif percentage > 80:
                color = (0.9, 0.7, 0.2, 0.4)
            else:
                color = (0.3, 0.8, 0.3, 0.4)
            
            with card.canvas.before:
                Color(*color)
                card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[8])
            card.bind(pos=lambda x, y: setattr(x.rect, 'pos', y),
                     size=lambda x, y: setattr(x.rect, 'size', y))
            
            card.add_widget(Label(text=f'[b]{category}[/b]', markup=True,
                                 font_size='16sp', size_hint_y=0.3))
            
            if budget_amount > 0:
                card.add_widget(Label(text=f'Budget: Rs. {budget_amount:,.2f} | Spent: Rs. {spent:,.2f}',
                                     font_size='13sp', size_hint_y=0.35))
                card.add_widget(Label(text=f'Remaining: Rs. {remaining:,.2f} ({percentage:.1f}%)',
                                     font_size='13sp', size_hint_y=0.35))
            else:
                card.add_widget(Label(text='No budget set', font_size='13sp',
                                     size_hint_y=0.7))
            
            self.budget_list.add_widget(card)
    
    def show_budget_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        category_spinner = Spinner(text='Select Category',
                                  values=['Food', 'Transport', 'Shopping',
                                         'Bills', 'Entertainment', 'Health',
                                         'Education', 'Other'],
                                  size_hint=(1, None), height=40)
        amount_input = TextInput(hint_text='Budget Amount', input_filter='float',
                               multiline=False, size_hint=(1, None), height=40)
        
        content.add_widget(category_spinner)
        content.add_widget(amount_input)
        
        set_btn = Button(text='Set Budget', size_hint=(1, None), height=40,
                        background_color=(0.2, 0.6, 1, 1))
        content.add_widget(set_btn)
        
        popup = Popup(title='Set Category Budget', content=content,
                     size_hint=(0.8, 0.4))
        
        def set_budget(x):
            try:
                category = category_spinner.text
                amount = float(amount_input.text)
                
                if category == 'Select Category':
                    return
                
                data = self.storage.load_data()
                if 'budgets' not in data:
                    data['budgets'] = {}
                data['budgets'][category] = amount
                self.storage.save_data(data)
                
                popup.dismiss()
                self.load_budgets()
            except:
                pass
        
        set_btn.bind(on_press=set_budget)
        popup.open()
    
    def refresh(self):
        self.build_ui()

# Main App
class ExpenseTrackerApp(App):
    def build(self):
        self.storage = SecureStorage()
        
        sm = ScreenManager()
        sm.add_widget(LoginScreen(self.storage, name='login'))
        sm.add_widget(DashboardScreen(self.storage, name='dashboard'))
        sm.add_widget(AddExpenseScreen(self.storage, name='add_expense'))
        sm.add_widget(AddIncomeScreen(self.storage, name='add_income'))
        sm.add_widget(LoansScreen(self.storage, name='loans'))
        sm.add_widget(SearchScreen(self.storage, name='search'))
        sm.add_widget(ReportsScreen(self.storage, name='reports'))
        sm.add_widget(BudgetScreen(self.storage, name='budget'))
        
        return sm

if __name__ == '__main__':
    ExpenseTrackerApp().run()