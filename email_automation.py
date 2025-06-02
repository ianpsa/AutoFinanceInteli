import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import logging
import json
from datetime import datetime
import webbrowser
from ascii_art import EMAIL_AUTOMATION_LOGO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='email_automation.log'
)
logger = logging.getLogger(__name__)

class EmailAutomationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Automation Tool")
        self.root.geometry("800x750") # Increased height for status label
        self.root.resizable(True, True)
        
        # Default recipients
        self.default_to = "central@inteli.edu.br, bianca.moretti@inteli.edu.br"
        self.default_cc = "lucas.niemeyer@inteli.edu.br, karina.santos@inteli.edu.br, financeiro@inteli.edu.br, larissa.almeida@inteli.edu.br"
        
        # Email history
        self.email_history = self.load_email_history()
        # Purchase history
        self.purchase_history = self.load_purchase_history()
        
        # Selenium WebDriver instance
        self.driver = None
        
        # Variables for multi-step UI
        self.drive_link_for_email = tk.StringVar()
        self.purchase_item_var = tk.StringVar()
        self.purchase_value_var = tk.StringVar()
        self.purchase_supplier_var = tk.StringVar()
        
        # Current purchase data storage
        self.current_purchase_data = {
            "item": "",
            "value": "",
            "supplier": "",
            "drive_link": ""
        }

        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        # Email form tab
        self.email_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.email_tab, text="Email Automation") # Renamed for clarity
        
        # History tab
        self.history_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.history_tab, text="Email History")

        # Purchase History tab
        self.purchase_history_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.purchase_history_tab, text="Purchase History")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Create the dynamic form UI in the email tab
        self.create_dynamic_email_ui_container()
        
        # Create the history view in the history tab
        self.create_history_view()
        # Create the purchase history view
        self.create_purchase_history_view()

    def _clear_scrollable_frame(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        # Re-add a title label if needed, or handle titles within each display method

    def _initialize_driver(self):
        if self.driver is None:
            logger.info("Initializing new WebDriver.")
            self.persistent_status_label.config(text="Initializing WebDriver...")
            self.root.update()
            try:
                chrome_options = Options()
                # chrome_options.add_argument("--headless") # Uncomment if you want headless
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_experimental_option("detach", True)
                
                # Use webdriver-manager to handle driver installation
                service = Service(ChromeDriverManager().install())
                
                # Initialize the driver with the service
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("WebDriver initialized successfully")
                self.persistent_status_label.config(text="WebDriver initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize WebDriver: {e}")
                self.persistent_status_label.config(text=f"WebDriver Error: {e}")
                messagebox.showerror("WebDriver Error", f"Failed to initialize WebDriver: {e}")
                self.driver = None
                raise
        else:
            logger.info("Reusing existing WebDriver instance.")
            self.persistent_status_label.config(text="Reusing existing WebDriver.")
        self.root.update()

    def _quit_driver(self):
        if self.driver:
            logger.info("Quitting WebDriver.")
            self.persistent_status_label.config(text="Quitting WebDriver...")
            self.root.update()
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error quitting WebDriver: {e}")
            finally:
                self.driver = None
                self.persistent_status_label.config(text="WebDriver quit.")
        else:
            self.persistent_status_label.config(text="No active WebDriver to quit.")
        self.root.update()

    def create_dynamic_email_ui_container(self):
        # This frame will hold the scrollable content area
        self.email_form_content_frame = ttk.Frame(self.email_tab, padding="10")
        self.email_form_content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # Canvas for scrollability
        self.canvas = tk.Canvas(self.email_form_content_frame)
        self.scrollbar = ttk.Scrollbar(self.email_form_content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas) # This is where dynamic content goes

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Persistent status label at the bottom of the email_tab
        self.persistent_status_label = ttk.Label(self.email_tab, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.persistent_status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        self.display_drive_link_input_ui() # Start with the first step

    def create_history_view(self):
        # Create a frame for the history view
        history_frame = ttk.Frame(self.history_tab, padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(history_frame, text="Email History", font=("Arial", 16, "bold"))
        title_label.pack(pady=10, anchor="w")
        
        # Create a treeview for the history
        columns = ("date", "club", "type", "recipient", "status")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        # Define headings
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("club", text="Club Name")
        self.history_tree.heading("type", text="Request Type")
        self.history_tree.heading("recipient", text="Recipient")
        self.history_tree.heading("status", text="Status")
        
        # Define columns
        self.history_tree.column("date", width=150)
        self.history_tree.column("club", width=150)
        self.history_tree.column("type", width=100)
        self.history_tree.column("recipient", width=200)
        self.history_tree.column("status", width=100)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate the history
        self.populate_history()
        
        # Add buttons for history management
        button_frame = ttk.Frame(history_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        refresh_button = ttk.Button(button_frame, text="Refresh", command=self.populate_history)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        export_button = ttk.Button(button_frame, text="Export History", command=self.export_history)
        export_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(button_frame, text="Clear History", command=self.clear_history)
        clear_button.pack(side=tk.LEFT, padx=5)

    def open_link(self, url):
        webbrowser.open(url)

    def display_drive_link_input_ui(self):
        self._clear_scrollable_frame()
        self.current_step_frame = ttk.Frame(self.scrollable_frame, padding="10") # Frame for this step
        self.current_step_frame.pack(fill=tk.BOTH, expand=True)

        # Título e instruções
        ttk.Label(self.current_step_frame, text="Etapa 1: Link do Drive e Acesso a Documentos", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")
        
        # Instruções detalhadas
        instructions_text = """Instruções para organização dos documentos:

1. Acesse o link: """
        
        instructions_label = ttk.Label(self.current_step_frame, text=instructions_text, wraplength=600, justify=tk.LEFT)
        instructions_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=10)
        
        # Link clicável
        drive_link = "https://drive.google.com/drive/u/1/folders/1eeBR_7tZnOFO-LFTGP-zvCN3qEFlkUnN"
        link_label = ttk.Label(self.current_step_frame, text=drive_link, foreground="blue", cursor="hand2")
        link_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        link_label.bind("<Button-1>", lambda e: self.open_link(drive_link))
        
        # Resto das instruções
        instructions_text2 = """
2. Entre na pasta do seu clube! Verifique se existe uma pasta do mês atual:
   - Se não existir, crie uma nova pasta com o número do mês atual e ano ex:(06.2025)

3. Dentro da pasta do mês:
   - Crie uma pasta com o nome do fornecedor
   - Em caso de reembolso, use o nome de quem fez a compra como fornecedor

4. Dentro da pasta do fornecedor:
   - Crie uma pasta com o nome da empresa onde foi feita a compra
   - Adicione os arquivos separadamente:
     * Nota fiscal
     * Comprovante de compra

5. Cole o link da pasta da empresa aqui abaixo:"""
        
        instructions_label2 = ttk.Label(self.current_step_frame, text=instructions_text2, wraplength=600, justify=tk.LEFT)
        instructions_label2.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
        
        ttk.Label(self.current_step_frame, text="Link do Drive (para o Email):").grid(row=4, column=0, sticky="w", pady=5)
        self.drive_link_for_email_entry = ttk.Entry(self.current_step_frame, width=60, textvariable=self.drive_link_for_email)
        self.drive_link_for_email_entry.grid(row=4, column=1, sticky="w", pady=5)
        
        confirm_button = ttk.Button(self.current_step_frame, text="Confirmar Link do Drive", command=self.process_drive_link_and_open_docs)
        confirm_button.grid(row=5, column=0, columnspan=2, pady=20)
        self.persistent_status_label.config(text="Aguardando link do Drive para o email.")

    def process_drive_link_and_open_docs(self):
        drive_link = self.drive_link_for_email.get()
        if not drive_link:
            messagebox.showerror("Erro", "Por favor, insira o link do Drive para o email.")
            self.persistent_status_label.config(text="Erro: Link do Drive não fornecido.")
            return

        # Link is now just confirmed and stored, no Selenium actions here.
        logger.info(f"Drive link for email confirmed: {drive_link}")
        self.persistent_status_label.config(text=f"Link do Drive confirmado: {drive_link[:50]}...")
        self.root.update()
        
        # No longer opening documents with Selenium here.
        # The self._initialize_driver() call is removed from this method.
        # WebDriver will be initialized later in send_email if needed.

        # Directly proceed to the next step
        self.display_purchase_info_ui()
        self.persistent_status_label.config(text="Link do Drive salvo. Prossiga para informações da compra.")

    def display_purchase_info_ui(self):
        self._clear_scrollable_frame()
        self.current_step_frame = ttk.Frame(self.scrollable_frame, padding="10")
        self.current_step_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.current_step_frame, text="Etapa 2: Informações da Compra (para Histórico)", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")

        ttk.Label(self.current_step_frame, text="Item da Compra:").grid(row=1, column=0, sticky="w", pady=5)
        self.purchase_item_entry = ttk.Entry(self.current_step_frame, width=60, textvariable=self.purchase_item_var)
        self.purchase_item_entry.grid(row=1, column=1, sticky="w", pady=5)
        # Add trace to update preview
        self.purchase_item_var.trace_add("write", lambda *args: self.update_preview())

        ttk.Label(self.current_step_frame, text="Valor da Compra (R$):").grid(row=2, column=0, sticky="w", pady=5)
        self.purchase_value_entry = ttk.Entry(self.current_step_frame, width=60, textvariable=self.purchase_value_var)
        self.purchase_value_entry.grid(row=2, column=1, sticky="w", pady=5)
        # Add trace to update preview
        self.purchase_value_var.trace_add("write", lambda *args: self.update_preview())

        ttk.Label(self.current_step_frame, text="Fornecedor da Compra:").grid(row=3, column=0, sticky="w", pady=5)
        self.purchase_supplier_entry = ttk.Entry(self.current_step_frame, width=60, textvariable=self.purchase_supplier_var)
        self.purchase_supplier_entry.grid(row=3, column=1, sticky="w", pady=5)
        # Add trace to update preview
        self.purchase_supplier_var.trace_add("write", lambda *args: self.update_preview())
        
        ttk.Label(self.current_step_frame, text="Link do Drive (Confirmado):").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Label(self.current_step_frame, text=self.drive_link_for_email.get() if self.drive_link_for_email.get() else "N/A", wraplength=400).grid(row=4, column=1, sticky="w", pady=5)

        conclude_button = ttk.Button(self.current_step_frame, text="Concluir Compra e Ir para Email", command=self.process_conclude_purchase)
        conclude_button.grid(row=5, column=0, columnspan=2, pady=20)
        self.persistent_status_label.config(text="Preencha as informações da compra.")

    def process_conclude_purchase(self):
        item = self.purchase_item_var.get()
        value = self.purchase_value_var.get()
        supplier = self.purchase_supplier_var.get()
        drive_link = self.drive_link_for_email.get()

        # DEBUG - verifique se os valores estão sendo capturados
        print(f"DEBUG - process_conclude_purchase - Valores capturados:")
        print(f"DEBUG - Item: '{item}'")
        print(f"DEBUG - Value: '{value}'")
        print(f"DEBUG - Supplier: '{supplier}'")
        print(f"DEBUG - Drive Link: '{drive_link}'")

        if not item or not value or not supplier:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos de informação da compra.")
            self.persistent_status_label.config(text="Erro: Campos da compra incompletos.")
            return

        # Save data to persistent structure
        self.current_purchase_data = {
            "item": item,
            "value": value,
            "supplier": supplier,
            "drive_link": drive_link
        }
        
        print(f"DEBUG - Dados salvos em current_purchase_data: {self.current_purchase_data}")

        purchase_data = {
            "drive_link": drive_link,
            "item": item,
            "value": value,
            "supplier": supplier
        }
        self.add_to_purchase_history(purchase_data)
        self.persistent_status_label.config(text="Informações da compra salvas no histórico.")
        
        # Removida a limpeza dos campos para manter os dados
        # self.purchase_item_var.set("")
        # self.purchase_value_var.set("")
        # self.purchase_supplier_var.set("")

        print("DEBUG - Chamando display_main_email_form_ui")
        self.display_main_email_form_ui()

    def display_main_email_form_ui(self):
        self._clear_scrollable_frame()
        form_frame = ttk.Frame(self.scrollable_frame, padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True)

        print("DEBUG - Iniciando display_main_email_form_ui")
        print(f"DEBUG - Dados atuais: {self.current_purchase_data}")

        ttk.Label(form_frame, text="Etapa 3: Compor e Enviar Email", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")
        
        # Recipients
        ttk.Label(form_frame, text="To:").grid(row=1, column=0, sticky="w", pady=5)
        self.to_entry = ttk.Entry(form_frame, width=60)
        self.to_entry.grid(row=1, column=1, sticky="w", pady=5)
        self.to_entry.insert(0, self.default_to)
        
        ttk.Label(form_frame, text="CC:").grid(row=2, column=0, sticky="w", pady=5)
        self.cc_entry = ttk.Entry(form_frame, width=60)
        self.cc_entry.grid(row=2, column=1, sticky="w", pady=5)
        self.cc_entry.insert(0, self.default_cc)
        
        # Club name
        ttk.Label(form_frame, text="Nome do Clube:").grid(row=3, column=0, sticky="w", pady=5)
        self.club_name_entry = ttk.Entry(form_frame, width=60)
        self.club_name_entry.grid(row=3, column=1, sticky="w", pady=5)
        # Add trace to update preview
        self.club_name_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        
        # Request type
        ttk.Label(form_frame, text="Tipo de Solicitação:").grid(row=4, column=0, sticky="w", pady=5)
        self.request_type = tk.StringVar(value="Pagamento")
        request_frame_inner = ttk.Frame(form_frame)
        request_frame_inner.grid(row=4, column=1, sticky="w", pady=5)
        
        ttk.Radiobutton(request_frame_inner, text="Pagamento", variable=self.request_type, value="Pagamento", command=self.update_preview).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(request_frame_inner, text="Reembolso", variable=self.request_type, value="Reembolso", command=self.update_preview).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(form_frame, text="Link (para email):").grid(row=8, column=0, sticky="w", pady=5)
        self.link_entry = ttk.Entry(form_frame, width=60)
        self.link_entry.grid(row=8, column=1, sticky="w", pady=5)
        self.link_entry.insert(0, self.current_purchase_data.get("drive_link", ""))
        # Add trace to update preview
        self.link_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        
        # Preview section
        ttk.Separator(form_frame, orient='horizontal').grid(row=12, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(form_frame, text="Email Preview", font=("Arial", 12, "bold")).grid(row=13, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Label(form_frame, text="Subject:").grid(row=14, column=0, sticky="w", pady=5)
        self.subject_preview = ttk.Label(form_frame, text="[Solicitação de Pagamento] - [Club Name] - [Request Type]")
        self.subject_preview.grid(row=14, column=1, sticky="w", pady=5)
        
        ttk.Label(form_frame, text="Body:").grid(row=15, column=0, sticky="nw", pady=5)
        self.body_preview = tk.Text(form_frame, width=45, height=8, wrap=tk.WORD)
        self.body_preview.grid(row=15, column=1, sticky="w", pady=5)
        
        # Update preview button
        self.update_preview_button = ttk.Button(form_frame, text="Update Preview", command=self.update_preview)
        self.update_preview_button.grid(row=16, column=0, columnspan=2, pady=10)
        
        # Send button
        self.send_button = ttk.Button(form_frame, text="Send Email", command=self.send_email)
        self.send_button.grid(row=17, column=0, columnspan=2, pady=10)
        
        # Back to Step 1 button
        back_to_start_button = ttk.Button(form_frame, text="Reiniciar (Voltar à Etapa 1)", command=self.display_drive_link_input_ui)
        back_to_start_button.grid(row=18, column=0, columnspan=2, pady=5)

        self.persistent_status_label.config(text="Preencha os detalhes do email.")
    
        # Forçar atualização do preview após criar todos os widgets
        print("DEBUG - Forçando atualização inicial do preview")
        self.update_preview()
    
    def update_preview(self):
        try:
            print("DEBUG - Iniciando update_preview")
            print(f"DEBUG - current_purchase_data: {self.current_purchase_data}")
            
            # Update subject preview only if we're in the email form
            if hasattr(self, 'club_name_entry') and hasattr(self, 'request_type'):
                club_name = self.club_name_entry.get() or "Club Name"
                request_type_val = self.request_type.get()
                subject = f"[Solicitação de Pagamento] - [{club_name}] - [{request_type_val}]"
                self.subject_preview.config(text=subject)
                print(f"DEBUG - Subject atualizado: {subject}")
        
            # Update body preview with saved purchase information
            item_val = self.current_purchase_data.get("item", "")
            supplier_val = self.current_purchase_data.get("supplier", "")
            value_val = self.current_purchase_data.get("value", "")
            link_val = self.current_purchase_data.get("drive_link", "")
            
            print(f"DEBUG - Valores recuperados do current_purchase_data:")
            print(f"DEBUG - Item: '{item_val}'")
            print(f"DEBUG - Supplier: '{supplier_val}'")
            print(f"DEBUG - Value: '{value_val}'")
            print(f"DEBUG - Link: '{link_val}'")
            
            # Format the body text with all information
            body_text = f"Item: {item_val}\nFornecedora: {supplier_val}\nValor: R$ {value_val}\nLink: {link_val}"
            print(f"DEBUG - Body text gerado: {body_text}")
            
            # Only update the preview text if we're in the email form
            if hasattr(self, 'body_preview'):
                print("DEBUG - Atualizando body_preview")
                self.body_preview.config(state="normal")
                self.body_preview.delete(1.0, tk.END)
                self.body_preview.insert(tk.END, body_text)
                self.body_preview.config(state="disabled")
                print("DEBUG - body_preview atualizado com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar preview: {str(e)}")
            print(f"DEBUG - Erro no update_preview: {str(e)}")
    
    def display_spreadsheet_instructions(self):
        # SALVAR VALORES ANTES DE LIMPAR A TELA
        club_name = self.club_name_entry.get() if hasattr(self, 'club_name_entry') and self.club_name_entry.winfo_exists() else "N/A"
        supplier = self.current_purchase_data.get("supplier", "N/A")
        value = self.current_purchase_data.get("value", "N/A")
        
        self._clear_scrollable_frame()
        spreadsheet_frame = ttk.Frame(self.scrollable_frame, padding="10")
        spreadsheet_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        ttk.Label(spreadsheet_frame, text="Preenchimento da Planilha", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")
        
        # Link clicável para a planilha
        spreadsheet_link = "https://docs.google.com/spreadsheets/d/1tcjKgxtn11jfg-J0z9MV6xNidyO6lAmo3KXOtuuG2ws/edit?gid=1655993304#gid=1655993304"
        link_label = ttk.Label(spreadsheet_frame, text=spreadsheet_link, foreground="blue", cursor="hand2")
        link_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        link_label.bind("<Button-1>", lambda e: self.open_link(spreadsheet_link))
        
        # Instruções detalhadas
        instructions_text = f"""Instruções para preenchimento da planilha:

1. Preencha as seguintes informações:
   - Solicitante: {club_name}
   - Responsável: "Financeiro Central Estudantil + Bianca Moretti"
   - Data da compra: (data da nota fiscal)
   - Fornecedor: {supplier}
   - Valor líquido: {value}
   - Valor bruto: (mesmo valor líquido)
   - Data de pagamento: 

2. Regras importantes para data de pagamento:
   - Para pagamentos:
     * Deve ser em até 15 dias ANTERIORMENTE à emissão do boleto
     * Verifique se o boleto não está com vencimento antes de 15 dias
     * Se o vencimento for antes de 15 dias:
       - Emita um novo boleto
       - Avise o financeiro alguns dias antes
   
   - Para reembolsos:
     * Deve ser 15 dias após o dia atual

3. Lembrete importante:
   - O financeiro só processa pagamentos com 15 dias de antecedência
   - Mantenha a planilha sempre atualizada
   - Verifique todas as informações antes de salvar"""
        
        instructions_label = ttk.Label(spreadsheet_frame, text=instructions_text, wraplength=600, justify=tk.LEFT)
        instructions_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        
        # Botão para voltar ao início
        back_button = ttk.Button(spreadsheet_frame, text="Voltar ao Início", command=self.display_drive_link_input_ui)
        back_button.grid(row=3, column=0, columnspan=2, pady=20)
        
        self.persistent_status_label.config(text="Aguardando preenchimento da planilha.")
    
    def send_email(self):
        # Validate inputs
        if not self.validate_inputs():
            self.persistent_status_label.config(text="Validação falhou. Verifique os campos.")
            return
        
        self.persistent_status_label.config(text="Preparando para compor email... Por favor, aguarde.")
        self.root.update()
        
        try:
            email_user = os.environ.get('EMAIL_USER')
            email_password = os.environ.get('EMAIL_PASSWORD')
            
            if not email_user or not email_password:
                messagebox.showerror("Error", "EMAIL_USER and EMAIL_PASSWORD environment variables must be set.")
                self.persistent_status_label.config(text="Erro: Variáveis de ambiente EMAIL_USER/PASSWORD não configuradas.")
                return
            
            self._initialize_driver() # Ensure driver is ready
            if not self.driver:
                self.persistent_status_label.config(text="Falha ao iniciar WebDriver para email. Verifique o log.")
                return

            self.persistent_status_label.config(text="WebDriver pronto. Fazendo login no Gmail...")
            self.root.update()

            # Navigate to Gmail
            self.driver.get("https://mail.google.com")
            logger.info("Navegando para Gmail...")
            
            # Wait for the email input field and log in
            email_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_input.send_keys(email_user)
            email_input.send_keys(Keys.RETURN)
            logger.info("Email/Usuário inserido...")
            self.persistent_status_label.config(text="Email/Usuário inserido...")
            self.root.update()

            # Wait for the password input field
            password_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            password_input.send_keys(email_password)
            password_input.send_keys(Keys.RETURN)
            logger.info("Senha inserida...")
            self.persistent_status_label.config(text="Senha inserida. Aguardando login...")
            self.root.update()
            
            # Após o login bem-sucedido, substituir esta parte:
            logger.info("Aguardando carregamento completo do Gmail...")
            self.persistent_status_label.config(text="Aguardando carregamento do Gmail...")
            self.root.update()
            
            # Aguardar o Gmail carregar completamente
            WebDriverWait(self.driver, 30).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-tooltip='Escrever']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.T-I.T-I-KE.L3"))
                )
            )
            
            logger.info("Gmail carregado. Procurando botão Escrever...")
            self.persistent_status_label.config(text="Procurando botão Escrever...")
            self.root.update()
            
            # Aguardar um pouco mais para garantir que tudo carregou
            time.sleep(3)
            
            # Tentar diferentes seletores para o botão Escrever
            compose_selectors = [
                "div.T-I.T-I-KE.L3",  # Classe padrão do botão
                "[data-tooltip='Escrever']",
                "div[role='button'][aria-label*='Escrever']",
                "//div[@role='button' and contains(text(), 'Escrever')]"
            ]
            
            compose_button = None
            for selector in compose_selectors:
                try:
                    if selector.startswith("//"):
                        compose_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        compose_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    break
                except:
                    continue
            
            if not compose_button:
                raise Exception("Não foi possível localizar o botão Escrever")
            
            # Rolar até o botão e clicar
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", compose_button)
            time.sleep(2)
            
            # Tentar clicar usando JavaScript se o clique normal falhar
            try:
                compose_button.click()
                logger.info("Botão clicado com sucesso")
            except Exception as e:
                logger.warning(f"Clique normal falhou, tentando JavaScript: {e}")
                self.driver.execute_script("arguments[0].click();", compose_button)
                logger.info("Botão clicado via JavaScript")
            
            self.persistent_status_label.config(text="Aguardando janela de composição...")
            self.root.update()
            
            # Aguardar janela de composição aparecer
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form[enctype='multipart/form-data']"))
            )
            
            # Aguardar a janela carregar completamente
            time.sleep(3)
            
            # Preencher destinatários
            logger.info("Procurando campo de destinatários...")
            to_field_selectors = [
                "input[aria-label='Destinatários']",  # Baseado no aria-label do HTML
                "input.agP.aFw",  # Classes específicas do input
                "input[peoplekit-id='BbVjBd']",  # ID específico do peoplekit
                "input[role='combobox'][aria-label*='Destinatários']"
            ]
            
            to_field = None
            for selector in to_field_selectors:
                try:
                    to_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if to_field:
                        break
                except:
                    continue
            
            if not to_field:
                raise Exception("Campo 'Para' não encontrado")
            
            to_field.clear()
            to_field.send_keys(self.to_entry.get())
            logger.info("Destinatários preenchidos")
            
            # Preencher CC (opcional)
            try:
                # Procurar e clicar no link CC/Cco
                cc_link = self.driver.find_element(By.CSS_SELECTOR, "span.aB.gQ.pE[aria-label*='Cc']")
                cc_link.click()
                time.sleep(1)
                
                # Aguardar campo CC aparecer
                cc_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[name='cc'] input"))
                )
                cc_field.clear()
                cc_field.send_keys(self.cc_entry.get())
                logger.info("CC preenchido")
            except Exception as e:
                logger.warning(f"Erro ao preencher CC (opcional): {str(e)}")
            # Preencher assunto
            logger.info("Preenchendo assunto...")
            subject_selectors = [
                "input[name='subjectbox']",  # Name específico do HTML
                "input.aoT",  # Classe específica
                "input[placeholder='Assunto']",
                "input[aria-label='Assunto']"
            ]
            
            subject_field = None
            for selector in subject_selectors:
                try:
                    subject_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if subject_field:
                        break
                except:
                    continue
            
            if not subject_field:
                raise Exception("Campo de assunto não encontrado")
            
            club_name_val = self.club_name_entry.get()
            request_type_val = self.request_type.get()
            subject_text = f"[Solicitação de Pagamento] - [{club_name_val}] - [{request_type_val}]"
            
            subject_field.clear()
            subject_field.send_keys(subject_text)
            logger.info("Assunto preenchido")
            
            # Preencher corpo do email
            logger.info("Preenchendo corpo do email...")
            body_selectors = [
                "div.Am.aiL.Al.editable.LW-avf.tS-tW",  # Classes específicas do HTML
                "div[aria-label='Corpo da mensagem'][contenteditable='true']",
                "div[role='textbox'][aria-label*='Corpo']",
                "div.editable[contenteditable='true']"
            ]
            
            body_field = None
            for selector in body_selectors:
                try:
                    body_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if body_field and body_field.is_displayed():
                        break
                except:
                    continue
            
            if not body_field:
                raise Exception("Campo de corpo do email não encontrado")
            
            # Limpar o campo e preencher
            time.sleep(1)  # Aguardar o campo estar pronto
            
            # Clicar no campo primeiro para garantir foco
            body_field.click()
            time.sleep(0.5)
            
            # Limpar conteúdo existente
            body_field.send_keys(Keys.CONTROL + "a")
            body_field.send_keys(Keys.DELETE)
            
            # Preencher com o conteúdo
            item_val = self.current_purchase_data.get("item", "")
            supplier_val = self.current_purchase_data.get("supplier", "")
            value_val = self.current_purchase_data.get("value", "")
            link_val = self.current_purchase_data.get("drive_link", "")
        
            body_text = f"Item: {item_val}\nFornecedora: {supplier_val}\nValor: R$ {value_val}\nLink: {link_val}"
        
            # Enviar o texto linha por linha para evitar problemas
            lines = body_text.split('\n')
            for i, line in enumerate(lines):
                body_field.send_keys(line)
                if i < len(lines) - 1:  # Não adicionar quebra após a última linha
                    body_field.send_keys(Keys.SHIFT + Keys.RETURN)
            
            logger.info("Corpo do email preenchido")

            # Sucesso
            self.persistent_status_label.config(text="Email composto com sucesso! Verifique e envie manualmente.")
            messagebox.showinfo("Sucesso", "Email composto com sucesso!\n\nPor favor, verifique o conteúdo e clique em 'Enviar' manualmente.")
            
            # Adicionar ao histórico
            self.add_to_history(club_name_val, request_type_val, self.to_entry.get(), "Composed")
            
            # Mostrar tela de instruções da planilha
            self.display_spreadsheet_instructions()

        except Exception as e:
            logger.error(f"Erro ao compor email: {str(e)}")
            self.persistent_status_label.config(text=f"Erro ao compor email: {str(e)[:100]}")
            messagebox.showerror("Error", f"Falha ao compor email: {str(e)}")
            
            # Add to history with error status
            self.add_to_history(
                self.club_name_entry.get() if hasattr(self, 'club_name_entry') else "N/A",
                self.request_type.get() if hasattr(self, 'request_type') else "N/A",
                self.to_entry.get() if hasattr(self, 'to_entry') else "N/A",
                f"Failed: {str(e)[:50]}..."
            )
        
        finally:
            # Don't quit the driver here, as the user needs to review and send the email
            self.persistent_status_label.config(text="Email composto. Aguardando envio manual pelo usuário.")
    
    def validate_inputs(self):
        # Check required fields for the email form specifically
        if not hasattr(self, 'club_name_entry') or not self.club_name_entry.get():
            messagebox.showerror("Validation Error", "Nome do Clube é obrigatório.")
            return False
        
        # Item, Supplier, Value are no longer direct inputs in the email form, so validation here is removed.
        # Their presence is ensured by the purchase info step.

        if not hasattr(self, 'link_entry') or not self.link_entry.get(): # This should be pre-filled
            messagebox.showerror("Validation Error", "Link (para email) é obrigatório.")
            return False
        
        return True
    
    def load_email_history(self):
        try:
            if os.path.exists("email_history.json"):
                with open("email_history.json", "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading email history: {str(e)}")
            return []
    
    def save_email_history(self):
        try:
            with open("email_history.json", "w") as f:
                json.dump(self.email_history, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving email history: {str(e)}")
    
    def add_to_history(self, club_name, request_type, recipient, status):
        # Create a new history entry
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "club": club_name,
            "type": request_type,
            "recipient": recipient,
            "status": status
        }
        
        # Add to the history list
        self.email_history.insert(0, entry)
        
        # Limit history to 100 entries
        if len(self.email_history) > 100:
            self.email_history = self.email_history[:100]
        
        # Save the updated history
        self.save_email_history()
        
        # Refresh the history view
        self.populate_history()
    
    def populate_history(self):
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Add history items
        for entry in self.email_history:
            self.history_tree.insert("", "end", values=(
                entry["date"],
                entry["club"],
                entry["type"],
                entry["recipient"],
                entry["status"]
            ))
    
    def export_history(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                title="Export History"
            )
            
            if not file_path:
                return
            
            with open(file_path, "w") as f:
                # Write header
                f.write("Date,Club Name,Request Type,Recipient,Status\n")
                
                # Write data
                for entry in self.email_history:
                    f.write(f"{entry['date']},{entry['club']},{entry['type']},{entry['recipient']},{entry['status']}\n")
            
            messagebox.showinfo("Export Successful", f"History exported to {file_path}")
        
        except Exception as e:
            logger.error(f"Error exporting history: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export history: {str(e)}")
    
    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the email history?"):
            self.email_history = []
            self.save_email_history()
            self.populate_history()
            messagebox.showinfo("History Cleared", "Email history has been cleared.")

    # --- Purchase History Methods ---
    def load_purchase_history(self):
        try:
            if os.path.exists("purchase_history.json"):
                with open("purchase_history.json", "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading purchase history: {str(e)}")
            return []

    def save_purchase_history(self):
        try:
            with open("purchase_history.json", "w") as f:
                json.dump(self.purchase_history, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving purchase history: {str(e)}")

    def add_to_purchase_history(self, purchase_data_dict):
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **purchase_data_dict
        }
        self.purchase_history.insert(0, entry)
        if len(self.purchase_history) > 200: # Limit purchase history
            self.purchase_history = self.purchase_history[:200]
        self.save_purchase_history()
        if hasattr(self, 'purchase_history_tree'): # Ensure tree exists
            self.populate_purchase_history_view()
            
    def create_purchase_history_view(self):
        p_history_frame = ttk.Frame(self.purchase_history_tab, padding="10")
        p_history_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(p_history_frame, text="Histórico de Compras", font=("Arial", 16, "bold"))
        title_label.pack(pady=10, anchor="w")
        
        columns = ("date", "drive_link", "item", "value", "supplier")
        self.purchase_history_tree = ttk.Treeview(p_history_frame, columns=columns, show="headings")
        
        self.purchase_history_tree.heading("date", text="Data")
        self.purchase_history_tree.heading("drive_link", text="Link Drive")
        self.purchase_history_tree.heading("item", text="Item Compra")
        self.purchase_history_tree.heading("value", text="Valor Compra")
        self.purchase_history_tree.heading("supplier", text="Fornecedor Compra")
        
        self.purchase_history_tree.column("date", width=150, anchor="w")
        self.purchase_history_tree.column("drive_link", width=200, anchor="w")
        self.purchase_history_tree.column("item", width=150, anchor="w")
        self.purchase_history_tree.column("value", width=100, anchor="w")
        self.purchase_history_tree.column("supplier", width=150, anchor="w")
        
        scrollbar = ttk.Scrollbar(p_history_frame, orient=tk.VERTICAL, command=self.purchase_history_tree.yview)
        self.purchase_history_tree.configure(yscroll=scrollbar.set)
        
        self.purchase_history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.populate_purchase_history_view()

        button_frame = ttk.Frame(p_history_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        refresh_button = ttk.Button(button_frame, text="Atualizar", command=self.populate_purchase_history_view)
        refresh_button.pack(side=tk.LEFT, padx=5)
        # Export/Clear for purchase history can be added similarly to email history if needed


    def populate_purchase_history_view(self):
        if not hasattr(self, 'purchase_history_tree'): return
        for item in self.purchase_history_tree.get_children():
            self.purchase_history_tree.delete(item)
        
        for entry in self.purchase_history:
            self.purchase_history_tree.insert("", "end", values=(
                entry.get("date", ""),
                entry.get("drive_link", ""),
                entry.get("item", ""),
                entry.get("value", ""),
                entry.get("supplier", "")
            ))

def main():
    # Exibir ASCII art
    print("\033[1;36m")  # Cor ciano brilhante
    print(EMAIL_AUTOMATION_LOGO)
    print("\033[0m")  # Resetar cor
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar se as variáveis de ambiente estão definidas
    if not os.getenv('EMAIL_USER') or not os.getenv('EMAIL_PASSWORD'):
        print("\033[1;31mErro: Variáveis de ambiente não configuradas!\033[0m")
        print("Por favor, crie um arquivo .env com suas credenciais do Gmail.")
        print("Exemplo:")
        print("EMAIL_USER=seu.email@gmail.com")
        print("EMAIL_PASSWORD=sua_senha_de_app")
        return

    root = tk.Tk()
    app = EmailAutomationTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
