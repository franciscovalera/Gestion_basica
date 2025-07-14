'''
Esto es un pequeño proyecto propio que esta pensado para serme util a mi mismo, con cambios minimos se puede adaptar a cualquier persona 
que quiera llevar un control de sus inversiones.

Este codigo es un gestor de inversiones en acciones y criptomonedas, con funcionalidades para registrar transacciones, 
consultar precios actuales y gestionar efectivo. Crea automaticamente todos los archivos necesarios.
'''



import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import os
from pathlib import Path
import yfinance as yf
from datetime import datetime

# Configuración inicial
SCRIPT_DIR = Path(__file__).resolve().parent 
DB_FILE = os.path.join(SCRIPT_DIR, "basedatosCY.csv")
ACCIONES_FILE = os.path.join(SCRIPT_DIR, "accionesCY.csv")
FIELDNAMES = ["id", "d", "m", "a", "cantidad", "trans"]
ACCIONES_FIELDS = ["simbolo", "cantidad", "precio_compra", "notas"]
VALID_TRANS = ['s', 'n']
MESES = {
    '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
    '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
    '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
}

lista_acciones = ['BTC-USD', 'ETH-USD', 'XRP-USD', 'ADA-USD', 'NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'SAN.MC', 'BBVA.MC', 'ITX.MC', 'REP.MC', 'IBE.MC', 'SPY', '^STOXX50E']

class StockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Inversiones")
        self.root.geometry("1000x700")
        
        # Variables
        self.efectivo = 0.0  # Valor temporal, será sobrescrito por cargar_efectivo()
        
        # Cargar datos iniciales
        self.inicializar_csv()
        self.cargar_efectivo()  # Ahora esto establece el valor correcto
    

        # Estilo
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        
        # Pestañas
        self.tab_control = ttk.Notebook(root)
        
        # Pestaña de Resumen
        self.tab_resumen = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_resumen, text='💰 Resumen')
        self.setup_resumen_tab()
        
        # Pestaña de Registros
        self.tab_registros = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_registros, text='📝 Registros')
        self.setup_registros_tab()
        
        # Pestaña de Acciones
        self.tab_acciones = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_acciones, text='📈 Acciones')
        self.setup_acciones_tab()
        
        # Pestaña de Efectivo
        self.tab_efectivo = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_efectivo, text='💵 Efectivo')
        self.setup_efectivo_tab()
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Cargar datos iniciales
        self.inicializar_csv()
        self.cargar_efectivo()
        self.actualizar_lista_registros()
        self.actualizar_lista_acciones()
        self.actualizar_info_acciones()
    
    # Funciones base de datos
    def inicializar_csv(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
                writer.writeheader()
                
        if not os.path.exists(ACCIONES_FILE):
            with open(ACCIONES_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=ACCIONES_FIELDS)
                writer.writeheader()

    def cargar_registros(self):
        try:
            with open(DB_FILE, mode='r', newline='', encoding='utf-8') as file:
                registros = list(csv.DictReader(file))
                if registros and 'id' not in registros[0]:
                    for i, r in enumerate(registros, 1):
                        r['id'] = str(i)
                return registros
        except FileNotFoundError:
            return []

    def cargar_acciones(self):
        try:
            with open(ACCIONES_FILE, mode='r', newline='', encoding='utf-8') as file:
                return list(csv.DictReader(file))
        except FileNotFoundError:
            return []

    def cargar_efectivo(self):
        try:
            with open(os.path.join(SCRIPT_DIR, "efectivoCY.txt"), 'r') as f:
                self.efectivo = float(f.read())
        except (FileNotFoundError, ValueError):
            # Si el archivo no existe o hay error en el formato, inicializar a 0
            self.efectivo = 0.0
            self.guardar_efectivo()  # Crear archivo con valor inicial
    
    def guardar_efectivo(self):
        with open(os.path.join(SCRIPT_DIR, "efectivoCY.txt"), 'w') as f:
            f.write(str(self.efectivo))

    def guardar_registros(self, registros):
        with open(DB_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(registros)

    def guardar_acciones(self, acciones):
        with open(ACCIONES_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=ACCIONES_FIELDS)
            writer.writeheader()
            writer.writerows(acciones)

    def obtener_proximo_id(self):
        registros = self.cargar_registros()
        if not registros:
            return 1
        return max(int(r['id']) for r in registros) + 1

    # Funciones acciones
    def precio_en_euros(self, simbolo):
        try:
            if simbolo.endswith('-USD') or simbolo in ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN']:
                accion = yf.Ticker(simbolo)
                usd_eur = yf.Ticker("EURUSD=X").history(period='1d')['Close'].iloc[-1]
                precio_usd = accion.history(period='1d')['Close'].iloc[-1]
                return precio_usd / usd_eur
            else:
                return yf.Ticker(simbolo).history(period='1d')['Close'].iloc[-1]
        except Exception as e:
            raise ValueError(f"Error al obtener precio: {str(e)}")

    # GUI Registros
    def setup_registros_tab(self):
        frame = ttk.Frame(self.tab_registros)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scroll_y = ttk.Scrollbar(frame, orient='vertical')
        scroll_x = ttk.Scrollbar(frame, orient='horizontal')
        
        self.tree = ttk.Treeview(frame, columns=('ID', 'Fecha', 'Cantidad', 'Trans'), 
                               yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
                               selectmode='browse')
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        self.tree.heading('ID', text='ID', anchor='center')
        self.tree.heading('Fecha', text='Fecha', anchor='center')
        self.tree.heading('Cantidad', text='Cantidad (€)', anchor='center')
        self.tree.heading('Trans', text='Transacción', anchor='center')
        
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Fecha', width=150, anchor='center')
        self.tree.column('Cantidad', width=100, anchor='e')
        self.tree.column('Trans', width=100, anchor='center')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        btn_frame = ttk.Frame(self.tab_registros)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(btn_frame, text="➕ Añadir", command=self.agregar_registro_gui).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✏️ Modificar", command=self.modificar_registro_gui).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Eliminar", command=self.eliminar_registro_gui).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Actualizar", command=self.actualizar_lista_registros).pack(side='right', padx=5)
    
    # GUI Acciones
    def setup_acciones_tab(self):
        # Frame para lista de acciones
        acciones_list_frame = ttk.LabelFrame(self.tab_acciones, text="Tus Acciones")
        acciones_list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scroll_y = ttk.Scrollbar(acciones_list_frame, orient='vertical')
        scroll_x = ttk.Scrollbar(acciones_list_frame, orient='horizontal')
        
        self.acciones_tree = ttk.Treeview(acciones_list_frame, 
                                        columns=('Símbolo', 'Cantidad', 'P. Compra', 'Valor Actual', 'Beneficio', 'Notas'), 
                                        yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
                                        selectmode='browse')
        
        scroll_y.config(command=self.acciones_tree.yview)
        scroll_x.config(command=self.acciones_tree.xview)
        
        self.acciones_tree.heading('Símbolo', text='Símbolo', anchor='center')
        self.acciones_tree.heading('Cantidad', text='Cantidad', anchor='center')
        self.acciones_tree.heading('P. Compra', text='P. Compra (€)', anchor='center')
        self.acciones_tree.heading('Valor Actual', text='Valor Actual (€)', anchor='center')
        self.acciones_tree.heading('Beneficio', text='Beneficio (€)', anchor='center')
        self.acciones_tree.heading('Notas', text='Notas', anchor='center')
        
        self.acciones_tree.column('Símbolo', width=100, anchor='center')
        self.acciones_tree.column('Cantidad', width=100, anchor='center')
        self.acciones_tree.column('P. Compra', width=100, anchor='center')
        self.acciones_tree.column('Valor Actual', width=100, anchor='center')
        self.acciones_tree.column('Beneficio', width=100, anchor='center')
        self.acciones_tree.column('Notas', width=200, anchor='w')
        
        self.acciones_tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        acciones_list_frame.grid_rowconfigure(0, weight=1)
        acciones_list_frame.grid_columnconfigure(0, weight=1)
        
        # Frame para botones de acciones
        acciones_btn_frame = ttk.Frame(self.tab_acciones)
        acciones_btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(acciones_btn_frame, text="➕ Añadir Acción", command=self.agregar_accion_gui).pack(side='left', padx=5)
        ttk.Button(acciones_btn_frame, text="✏️ Modificar", command=self.modificar_accion_gui).pack(side='left', padx=5)
        ttk.Button(acciones_btn_frame, text="🗑️ Eliminar", command=self.eliminar_accion_gui).pack(side='left', padx=5)
        ttk.Button(acciones_btn_frame, text="🔄 Actualizar", command=self.actualizar_lista_acciones).pack(side='right', padx=5)
        
        # Frame de consulta
        consulta_frame = ttk.LabelFrame(self.tab_acciones, text="Consultar Acción/Cripto")
        consulta_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(consulta_frame, text="Símbolo:").pack(side='left', padx=5)
        self.simbolo_entry = ttk.Entry(consulta_frame, width=15)
        self.simbolo_entry.pack(side='left', padx=5)
        self.simbolo_entry.insert(0, "NVDA")
        
        ttk.Button(consulta_frame, text="Buscar", command=self.consultar_accion).pack(side='left', padx=5)
        
        # Resultados
        self.resultado_frame = ttk.LabelFrame(self.tab_acciones, text="Información")
        self.resultado_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.resultado_text = tk.Text(self.resultado_frame, height=10, wrap=tk.WORD)
        scroll = ttk.Scrollbar(self.resultado_frame, command=self.resultado_text.yview)
        self.resultado_text.config(yscrollcommand=scroll.set)
        
        self.resultado_text.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        
        # Configurar texto
        self.resultado_text.tag_configure('title', font=('Arial', 12, 'bold'))
        self.resultado_text.tag_configure('positive', foreground='green')
        self.resultado_text.tag_configure('negative', foreground='red')
    
    # GUI Efectivo
    def setup_efectivo_tab(self):
        frame = ttk.Frame(self.tab_efectivo)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Mostrar efectivo actual
        self.efectivo_label = ttk.Label(frame, text=f"Efectivo disponible: {self.efectivo:.2f} €", font=('Arial', 14))
        self.efectivo_label.pack(pady=20)
        
        # Frame para operaciones
        operaciones_frame = ttk.LabelFrame(frame, text="Operaciones")
        operaciones_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(operaciones_frame, text="Ingresar efectivo", command=lambda: self.operacion_efectivo('ingreso')).pack(side='left', padx=5, pady=5, fill='x', expand=True)
        ttk.Button(operaciones_frame, text="Retirar efectivo", command=lambda: self.operacion_efectivo('retiro')).pack(side='left', padx=5, pady=5, fill='x', expand=True)
        ttk.Button(operaciones_frame, text="Establecer efectivo", command=lambda: self.operacion_efectivo('establecer')).pack(side='left', padx=5, pady=5, fill='x', expand=True)
    
    def operacion_efectivo(self, tipo):
        if tipo == 'ingreso':
            titulo = "Ingresar efectivo"
            mensaje = "Cantidad a ingresar:"
        elif tipo == 'retiro':
            titulo = "Retirar efectivo"
            mensaje = "Cantidad a retirar:"
        else:
            titulo = "Establecer efectivo"
            mensaje = "Nuevo saldo:"
        
        cantidad = simpledialog.askfloat(titulo, mensaje, parent=self.root)
        if cantidad is not None:
            try:
                if tipo == 'ingreso':
                    self.efectivo += cantidad
                elif tipo == 'retiro':
                    if cantidad > self.efectivo:
                        messagebox.showerror("Error", "No hay suficiente efectivo")
                        return
                    self.efectivo -= cantidad
                else:
                    self.efectivo = cantidad
                
                self.guardar_efectivo()
                self.actualizar_efectivo_display()
                self.actualizar_resumen()
                messagebox.showinfo("Éxito", f"Operación realizada. Nuevo saldo: {self.efectivo:.2f} €")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo realizar la operación: {str(e)}")
    
    def actualizar_efectivo_display(self):
        self.efectivo_label.config(text=f"Efectivo disponible: {self.efectivo:.2f} €")
    
    # GUI Resumen
    def setup_resumen_tab(self):
        resumen_frame = ttk.LabelFrame(self.tab_resumen, text="Resumen Financiero")
        resumen_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.resumen_text = tk.Text(resumen_frame, height=15, wrap=tk.WORD)
        scroll = ttk.Scrollbar(resumen_frame, command=self.resumen_text.yview)
        self.resumen_text.config(yscrollcommand=scroll.set)
        
        self.resumen_text.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        
        # Configurar texto
        self.resumen_text.tag_configure('header', font=('Arial', 32, 'bold'))
        self.resumen_text.tag_configure('positive', foreground='green', font=('Arial', 16, 'bold'))
        self.resumen_text.tag_configure('negative', foreground='red', font=('Arial', 16, 'bold'))
        self.resumen_text.tag_configure('text', font=('Arial', 20))
        self.resumen_text.tag_configure('highlight', font=('Arial', 28, 'bold'))
        
        # Actualizar periódicamente
        self.actualizar_resumen()
    
    # Funciones GUI Acciones
    def actualizar_lista_acciones(self):
        for i in self.acciones_tree.get_children():
            self.acciones_tree.delete(i)
        
        acciones = self.cargar_acciones()
        for accion in acciones:
            try:
                simbolo = accion['simbolo']
                cantidad = float(accion['cantidad'])
                precio_compra = float(accion['precio_compra'])
                precio_actual = self.precio_en_euros(simbolo)
                valor_actual = cantidad * precio_actual
                beneficio = valor_actual - (cantidad * precio_compra)
                notas = accion.get('notas', '')
                
                self.acciones_tree.insert('', 'end', values=(
                    simbolo,
                    f"{cantidad:.5f}",
                    f"{precio_compra:.4f}",
                    f"{valor_actual:.2f}",
                    f"{beneficio:.2f}",
                    notas
                ))
            except Exception as e:
                print(f"Error al cargar acción {accion.get('simbolo', '')}: {str(e)}")
    
    def agregar_accion_gui(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Añadir Acción")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Símbolo:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        simbolo_entry = ttk.Entry(dialog)
        simbolo_entry.grid(row=0, column=1, sticky='w')
        
        ttk.Label(dialog, text="Cantidad:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        cantidad_entry = ttk.Entry(dialog)
        cantidad_entry.grid(row=1, column=1, sticky='w')
        
        ttk.Label(dialog, text="Precio compra (€):").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        precio_entry = ttk.Entry(dialog)
        precio_entry.grid(row=2, column=1, sticky='w')
        
        ttk.Label(dialog, text="Notas:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        notas_entry = ttk.Entry(dialog)
        notas_entry.grid(row=3, column=1, sticky='w')
        
        def guardar():
            try:
                simbolo = simbolo_entry.get().strip().upper()
                cantidad = float(cantidad_entry.get())
                precio_compra = float(precio_entry.get())
                notas = notas_entry.get()
                
                if cantidad <= 0 or precio_compra <= 0:
                    raise ValueError("Cantidad y precio deben ser positivos")
                
                # Verificar que el símbolo existe
                try:
                    self.precio_en_euros(simbolo)
                except Exception as e:
                    raise ValueError(f"Símbolo no válido: {str(e)}")
                
                acciones = self.cargar_acciones()
                acciones.append({
                    'simbolo': simbolo,
                    'cantidad': str(cantidad),
                    'precio_compra': str(precio_compra),
                    'notas': notas
                })
                
                self.guardar_acciones(acciones)
                self.actualizar_lista_acciones()
                self.actualizar_resumen()
                dialog.destroy()
                messagebox.showinfo("Éxito", "Acción añadida correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Datos inválidos: {str(e)}")
        
        ttk.Button(dialog, text="Guardar", command=guardar).grid(row=4, column=1, pady=10, sticky='e')
    
    def modificar_accion_gui(self):
        seleccion = self.acciones_tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una acción para modificar")
            return
        
        item = self.acciones_tree.item(seleccion[0])
        valores = item['values']
        simbolo_original = valores[0]
        
        acciones = self.cargar_acciones()
        accion = next((a for a in acciones if a['simbolo'] == simbolo_original), None)
        
        if not accion:
            messagebox.showerror("Error", "Acción no encontrada")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Modificar Acción {simbolo_original}")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Símbolo:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        simbolo_entry = ttk.Entry(dialog)
        simbolo_entry.insert(0, accion['simbolo'])
        simbolo_entry.grid(row=0, column=1, sticky='w')
        
        ttk.Label(dialog, text="Cantidad:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        cantidad_entry = ttk.Entry(dialog)
        cantidad_entry.insert(0, accion['cantidad'])
        cantidad_entry.grid(row=1, column=1, sticky='w')
        
        ttk.Label(dialog, text="Precio compra (€):").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        precio_entry = ttk.Entry(dialog)
        precio_entry.insert(0, accion['precio_compra'])
        precio_entry.grid(row=2, column=1, sticky='w')
        
        ttk.Label(dialog, text="Notas:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        notas_entry = ttk.Entry(dialog)
        notas_entry.insert(0, accion.get('notas', ''))
        notas_entry.grid(row=3, column=1, sticky='w')
        
        def guardar():
            try:
                simbolo = simbolo_entry.get().strip().upper()
                cantidad = float(cantidad_entry.get())
                precio_compra = float(precio_entry.get())
                notas = notas_entry.get()
                
                if cantidad <= 0 or precio_compra <= 0:
                    raise ValueError("Cantidad y precio deben ser positivos")
                
                # Verificar que el símbolo existe (excepto si no cambió)
                if simbolo != simbolo_original:
                    try:
                        self.precio_en_euros(simbolo)
                    except Exception as e:
                        raise ValueError(f"Símbolo no válido: {str(e)}")
                
                accion.update({
                    'simbolo': simbolo,
                    'cantidad': str(cantidad),
                    'precio_compra': str(precio_compra),
                    'notas': notas
                })
                
                self.guardar_acciones(acciones)
                self.actualizar_lista_acciones()
                self.actualizar_resumen()
                dialog.destroy()
                messagebox.showinfo("Éxito", "Acción modificada correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Datos inválidos: {str(e)}")
        
        ttk.Button(dialog, text="Guardar", command=guardar).grid(row=4, column=1, pady=10, sticky='e')
    
    def eliminar_accion_gui(self):
        seleccion = self.acciones_tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una acción para eliminar")
            return
        
        item = self.acciones_tree.item(seleccion[0])
        simbolo = item['values'][0]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar la acción {simbolo}?"):
            acciones = self.cargar_acciones()
            acciones = [a for a in acciones if a['simbolo'] != simbolo]
            
            self.guardar_acciones(acciones)
            self.actualizar_lista_acciones()
            self.actualizar_resumen()
            messagebox.showinfo("Éxito", "Acción eliminada correctamente")
    
    # Funciones GUI Registros (sin cambios respecto a tu versión original)
    def actualizar_lista_registros(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        registros = self.cargar_registros()
        for r in registros:
            fecha = f"{r['d']}/{MESES.get(r['m'], r['m'])}/{r['a']}"
            trans = 'Sí' if r['trans'] == 's' else 'No'
            self.tree.insert('', 'end', values=(r['id'], fecha, f"{float(r['cantidad']):.2f} €", trans))
    
    def agregar_registro_gui(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Añadir Registro")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Fecha:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        
        frame_fecha = ttk.Frame(dialog)
        frame_fecha.grid(row=0, column=1, sticky='w')
        
        ttk.Label(frame_fecha, text="Día:").pack(side='left')
        dia_entry = ttk.Entry(frame_fecha, width=3)
        dia_entry.pack(side='left')
        
        ttk.Label(frame_fecha, text="Mes:").pack(side='left', padx=5)
        mes_entry = ttk.Entry(frame_fecha, width=3)
        mes_entry.pack(side='left')
        
        ttk.Label(frame_fecha, text="Año:").pack(side='left', padx=5)
        anio_entry = ttk.Entry(frame_fecha, width=5)
        anio_entry.pack(side='left')
        
        ttk.Label(dialog, text="Cantidad (€):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        cantidad_entry = ttk.Entry(dialog)
        cantidad_entry.grid(row=1, column=1, sticky='w')
        
        ttk.Label(dialog, text="Transacción realizada:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        tipo_var = tk.StringVar(value='s')
        ttk.Radiobutton(dialog, text="Sí", variable=tipo_var, value='s').grid(row=2, column=1, sticky='w')
        ttk.Radiobutton(dialog, text="No", variable=tipo_var, value='n').grid(row=3, column=1, sticky='w')
        
        def guardar():
            try:
                d = dia_entry.get().zfill(2)
                m = mes_entry.get().zfill(2)
                a = anio_entry.get()
                
                if not (d.isdigit() and m.isdigit() and a.isdigit()):
                    raise ValueError("La fecha debe contener solo números")
                
                if m not in MESES:
                    raise ValueError("Mes inválido. Use 01-12")
                
                cantidad = float(cantidad_entry.get())
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser positiva")
                
                registros = self.cargar_registros()
                nuevo_id = self.obtener_proximo_id()
                
                registros.append({
                    'id': str(nuevo_id),
                    'd': d,
                    'm': m,
                    'a': a,
                    'cantidad': str(cantidad),
                    'trans': tipo_var.get()
                })
                
                self.guardar_registros(registros)
                self.actualizar_lista_registros()
                self.actualizar_resumen()
                dialog.destroy()
                messagebox.showinfo("Éxito", "Registro añadido correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Datos inválidos: {str(e)}")
        
        ttk.Button(dialog, text="Guardar", command=guardar).grid(row=4, column=1, pady=10, sticky='e')
    
    def modificar_registro_gui(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un registro para modificar")
            return
        
        item = self.tree.item(seleccion[0])
        id_registro = item['values'][0]
        
        registros = self.cargar_registros()
        registro = next((r for r in registros if int(r['id']) == id_registro), None)
        
        if not registro:
            messagebox.showerror("Error", "Registro no encontrado")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Modificar Registro {id_registro}")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Fecha:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        
        frame_fecha = ttk.Frame(dialog)
        frame_fecha.grid(row=0, column=1, sticky='w')
        
        ttk.Label(frame_fecha, text="Día:").pack(side='left')
        dia_entry = ttk.Entry(frame_fecha, width=3)
        dia_entry.insert(0, registro['d'])
        dia_entry.pack(side='left')
        
        ttk.Label(frame_fecha, text="Mes:").pack(side='left', padx=5)
        mes_entry = ttk.Entry(frame_fecha, width=3)
        mes_entry.insert(0, registro['m'])
        mes_entry.pack(side='left')
        
        ttk.Label(frame_fecha, text="Año:").pack(side='left', padx=5)
        anio_entry = ttk.Entry(frame_fecha, width=5)
        anio_entry.insert(0, registro['a'])
        anio_entry.pack(side='left')
        
        ttk.Label(dialog, text="Cantidad (€):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        cantidad_entry = ttk.Entry(dialog)
        cantidad_entry.insert(0, registro['cantidad'])
        cantidad_entry.grid(row=1, column=1, sticky='w')
        
        ttk.Label(dialog, text="Transacción realizada:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        tipo_var = tk.StringVar(value=registro['trans'])
        ttk.Radiobutton(dialog, text="Sí", variable=tipo_var, value='s').grid(row=2, column=1, sticky='w')
        ttk.Radiobutton(dialog, text="No", variable=tipo_var, value='n').grid(row=3, column=1, sticky='w')
        
        def guardar():
            try:
                d = dia_entry.get().zfill(2)
                m = mes_entry.get().zfill(2)
                a = anio_entry.get()
                
                if not (d.isdigit() and m.isdigit() and a.isdigit()):
                    raise ValueError("La fecha debe contener solo números")
                
                if m not in MESES:
                    raise ValueError("Mes inválido. Use 01-12")
                
                cantidad = float(cantidad_entry.get())
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser positiva")
                
                registro.update({
                    'd': d,
                    'm': m,
                    'a': a,
                    'cantidad': str(cantidad),
                    'trans': tipo_var.get()
                })
                
                self.guardar_registros(registros)
                self.actualizar_lista_registros()
                self.actualizar_resumen()
                dialog.destroy()
                messagebox.showinfo("Éxito", "Registro modificado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Datos inválidos: {str(e)}")
        
        ttk.Button(dialog, text="Guardar", command=guardar).grid(row=4, column=1, pady=10, sticky='e')
    
    def eliminar_registro_gui(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un registro para eliminar")
            return
        
        item = self.tree.item(seleccion[0])
        id_registro = item['values'][0]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar el registro {id_registro}?"):
            registros = self.cargar_registros()
            registros = [r for r in registros if int(r['id']) != id_registro]
            
            self.guardar_registros(registros)
            self.actualizar_lista_registros()
            self.actualizar_resumen()
            messagebox.showinfo("Éxito", "Registro eliminado correctamente")
    
    def consultar_accion(self):
        simbolo = self.simbolo_entry.get().strip().upper()
        if not simbolo:
            messagebox.showwarning("Advertencia", "Ingrese un símbolo válido")
            return
        
        try:
            precio = self.precio_en_euros(simbolo)
            
            self.resultado_text.config(state=tk.NORMAL)
            self.resultado_text.delete(1.0, tk.END)
            
            self.resultado_text.insert(tk.END, f"{simbolo}\n", 'title')
            self.resultado_text.insert(tk.END, f"\nPrecio actual: {precio:.4f} €\n")
            
            if '-' in simbolo:
                ticker = yf.Ticker(simbolo)
                info = ticker.info
                
                self.resultado_text.insert(tk.END, "\nInformación:\n", 'title')
                self.resultado_text.insert(tk.END, f"Nombre: {info.get('shortName', 'N/A')}\n")
                self.resultado_text.insert(tk.END, f"Cambio 24h: {info.get('regularMarketChangePercent', 'N/A')}%\n")
                
                cambio = info.get('regularMarketChangePercent', 0)
                if isinstance(cambio, (int, float)):
                    tag = 'positive' if cambio >= 0 else 'negative'
                    self.resultado_text.insert(tk.END, f"{'▲' if cambio >=0 else '▼'} {abs(cambio):.2f}%\n", tag)
            
            self.resultado_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener información para {simbolo}:\n{str(e)}")
    
    def actualizar_info_acciones(self):
        self.actualizar_lista_acciones()
        self.root.after(15000, self.actualizar_info_acciones)
    
    def actualizar_resumen(self):
        registros = self.cargar_registros()
        total_invertido = 0.0
        
        for r in registros:
            cantidad = float(r['cantidad'])
            if r['trans'] == 's':  # Sí
                total_invertido += cantidad
            else:  # No
                total_invertido += 1.01 * cantidad

        total_invertido = round(total_invertido, 2)
        
        # Calcular valor de las acciones
        acciones = self.cargar_acciones()
        valor_total_acciones = 0.0
        beneficio_total = 0.0
        detalles_acciones = []
        
        for accion in acciones:
            try:
                simbolo = accion['simbolo']
                cantidad = float(accion['cantidad'])
                precio_compra = float(accion['precio_compra'])
                precio_actual = self.precio_en_euros(simbolo)
                valor_accion = cantidad * precio_actual
                valor_compra = cantidad * precio_compra
                beneficio = valor_accion - valor_compra
                
                valor_total_acciones += valor_accion
                beneficio_total += beneficio
                
                detalles_acciones.append(
                    f"{simbolo}: {cantidad:.5f} acciones\n"
                    f"  Compra: {valor_compra:.2f} € | Actual: {valor_accion:.2f} €\n"
                    f"  Beneficio: {beneficio:.2f} € ({beneficio/valor_compra*100:.2f}%)\n"
                )
            except Exception as e:
                print(f"Error al calcular valor de {accion.get('simbolo', '')}: {str(e)}")
        
        patrimonio = valor_total_acciones + self.efectivo
        balance_total = valor_total_acciones - total_invertido + self.efectivo
        porcentaje_total = (balance_total / total_invertido) * 100 if total_invertido != 0 else 0
        
        self.resumen_text.config(state=tk.NORMAL)
        self.resumen_text.delete(1.0, tk.END)
        
        self.resumen_text.insert(tk.END, "Resumen de Inversión\n", 'header')
        self.resumen_text.insert(tk.END, f"Patrimonio total: {patrimonio:.2f} €\n", 'highlight')
        
        self.resumen_text.insert(tk.END, "\nEfectivo disponible: ", 'text')
        self.resumen_text.insert(tk.END, f"{self.efectivo:.2f} €\n", 'positive' if self.efectivo >= 0 else 'negative')
        
        self.resumen_text.insert(tk.END, f"\nTotal invertido: {total_invertido:.2f} €\n", 'text')
        self.resumen_text.insert(tk.END, f"Valor total acciones: {valor_total_acciones:.2f} €\n", 'text')
        
        self.resumen_text.insert(tk.END, "\nBalance total: ", 'header')
        tag_total = 'positive' if balance_total >= 0 else 'negative'
        self.resumen_text.insert(tk.END, f"{balance_total:.2f} € ({porcentaje_total:.2f}%)\n", tag_total)
        
        self.resumen_text.insert(tk.END, "\nBeneficio total: ", 'header')
        tag_beneficio = 'positive' if beneficio_total >= 0 else 'negative'
        self.resumen_text.insert(tk.END, f"{beneficio_total:.2f} €\n", tag_beneficio)
        
        self.resumen_text.insert(tk.END, "\nDetalles por acción:\n", 'header')
        for detalle in detalles_acciones:
            self.resumen_text.insert(tk.END, detalle + "\n")
        
        self.resumen_text.config(state=tk.DISABLED)
        
        # Actualizar cada 15 segundos
        self.root.after(15000, self.actualizar_resumen)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = StockApp(root)
        
        try:
            root.iconbitmap(default='icon.ico')
        except:
            pass
        
        root.mainloop()
    
    except Exception as e:
        print(f"Error inicial: {str(e)}")