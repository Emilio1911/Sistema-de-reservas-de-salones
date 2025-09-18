import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from tkcalendar import DateEntry
import sqlite3
import os
from fpdf import FPDF

import sqlite3
from datetime import datetime, date, timedelta

class ReservaDatabase:
    """Gestiona todas las operaciones con la base de datos SQLite."""
    def __init__(self, db_path="reservas.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos y crea la tabla si no existe."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    salon TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    hora_inicio TEXT NOT NULL,
                    hora_fin TEXT NOT NULL,
                    solicitante TEXT NOT NULL,
                    contacto TEXT NOT NULL,
                    correo TEXT NOT NULL,
                    motivo TEXT NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error de Base de Datos: {str(e)}")
    
    def get_reservas_dia(self, salon, fecha):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, hora_inicio, hora_fin, solicitante FROM reservas 
                WHERE salon = ? AND fecha = ?
                ORDER BY hora_inicio
            ''', (salon, fecha))
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            print(f"Error al obtener reservas del día: {e}")
            return []
    
    def get_all_reservas(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reservas ORDER BY fecha_creacion DESC')
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            print(f"Error al obtener todas las reservas: {e}")
            return []

    def search_reservas(self, id_reserva="", solicitante="", salon="", fecha=""):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM reservas WHERE 1=1"
            params = []
            
            if id_reserva:
                query += " AND id = ?"
                params.append(id_reserva)
            else:
                if solicitante:
                    query += " AND solicitante LIKE ?"
                    params.append(f"%{solicitante}%")
                if salon:
                    query += " AND salon = ?"
                    params.append(salon)
                if fecha:
                    query += " AND fecha = ?"
                    params.append(fecha)
            
            query += " ORDER BY fecha_creacion DESC"
            
            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            print(f"Error al buscar reservas: {e}")
            return []

    def get_reserva_details(self, reserva_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reservas WHERE id = ?', (reserva_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            print(f"Error al obtener detalles de la reserva: {e}")
            return None

    def delete_reserva(self, reserva_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reservas WHERE id = ?', (reserva_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al eliminar reserva: {e}")
            return False

    def verificar_disponibilidad(self, salon, fecha, hora_inicio, hora_fin):
        try:
            inicio_nuevo = datetime.strptime(f"{fecha} {hora_inicio}", "%Y-%m-%d %H:%M")
            fin_nuevo = datetime.strptime(f"{fecha} {hora_fin}", "%Y-%m-%d %H:%M")
            if fin_nuevo <= inicio_nuevo:
                fin_nuevo += timedelta(days=1)
            
            reservas = self.get_reservas_dia(salon, fecha) # Se corrigió la llamada a un método de la propia clase
            for _, h_inicio, h_fin, _ in reservas:
                inicio_existente = datetime.strptime(f"{fecha} {h_inicio}", "%Y-%m-%d %H:%M")
                fin_existente = datetime.strptime(f"{fecha} {h_fin}", "%Y-%m-%d %H:%M")
                if fin_existente <= inicio_existente:
                    fin_existente += timedelta(days=1)
                
                if (inicio_nuevo < fin_existente) and (fin_nuevo > inicio_existente):
                    return False
            return True
        except Exception as e:
            print(f"Error al verificar disponibilidad: {e}")
            return False
    
    def guardar_reserva(self, salon, fecha, hora_inicio, hora_fin, solicitante, contacto, correo, motivo):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reservas (salon, fecha, hora_inicio, hora_fin, solicitante, contacto, correo, motivo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (salon, fecha, hora_inicio, hora_fin, solicitante, contacto, correo, motivo))
            conn.commit()
            reserva_id = cursor.lastrowid
            conn.close()
            return reserva_id
        except Exception as e:
            print(f"Error al guardar reserva: {e}")
            return None
        
class SistemaReservas:
    def __init__(self, debug=False):
        self.root = tk.Tk()
        self.root.title("Sistema de Reservas - Salones")
        self.root.configure(bg="#2c3e50")
        
        # === CAMBIO SOLICITADO: VENTANA PRINCIPAL EN PANTALLA COMPLETA ===
        self.root.state('zoomed')

        self.db = ReservaDatabase()
        self.salon_actual = None
        self.fecha_actual = date.today()
        self.mapa_reservas_lista = {}
        self.hora_inicio_seleccionada = None
        self.debug = debug
        
        self.setup_gui()
    
    def centrar_ventana(self, ventana, ancho, alto):
        screen_width = ventana.winfo_screenwidth()
        screen_height = ventana.winfo_screenheight()
        x = (screen_width - ancho) // 2
        y = (screen_height - alto) // 2
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
    
    def setup_gui(self):
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Sistema de Reservas de Salones", 
                 font=("Arial", 18, "bold"), bg="#2c3e50", fg="white").pack(pady=(0, 20))
        
        self.form_frame = tk.LabelFrame(main_frame, text="Reservas", font=("Arial", 12, "bold"), 
                                         bg="#34495e", fg="white", padx=15, pady=15)
        self.form_frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_form()
    
    def setup_form(self):
        left_frame = tk.Frame(self.form_frame, bg="#34495e")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 20))
        
        tk.Label(left_frame, text="Horarios del Día", font=("Arial", 11, "bold"), 
                 bg="#34495e", fg="white").pack(pady=(0, 5))
        
        fecha_frame = tk.Frame(left_frame, bg="#34495e")
        fecha_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(fecha_frame, text="Fecha:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.fecha_entry = DateEntry(fecha_frame, width=12, date_pattern='y-mm-dd',
                                     background='darkblue', foreground='white', borderwidth=2)
        self.fecha_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.fecha_entry.bind('<<DateEntrySelected>>', self.on_fecha_change)

        tk.Button(fecha_frame, text="Hoy", command=self.set_fecha_hoy, 
                  bg="#FFC107", padx=10).pack(side=tk.LEFT)
        
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.horarios_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Courier", 11), height=24, width=40)
        self.horarios_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.horarios_list.yview)
        
        self.horarios_list.bind('<Double-Button-1>', self.on_horario_select)
        self.horarios_list.bind('<Button-3>', self.show_context_menu)
        
        right_frame = tk.Frame(self.form_frame, bg="#34495e")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        campos = [("Hora Inicio:", "hora_inicio"), ("Hora Fin:", "hora_fin"),
                  ("Solicitante:", "solicitante"), ("Contacto:", "contacto"), ("Correo:", "correo")]
        self.entries = {}
        horas_disponibles = [f"{h:02d}:00" for h in range(24)]
        
        for label, key in campos:
            frame = tk.Frame(right_frame, bg="#34495e")
            frame.pack(fill=tk.X, pady=5)
            tk.Label(frame, text=label, width=12, anchor="w", bg="#34495e", fg="white").pack(side=tk.LEFT)
            
            if "hora" in key:
                entry = ttk.Combobox(frame, font=("Arial", 11), width=8, values=horas_disponibles)
            else:
                entry = tk.Entry(frame, font=("Arial", 11), width=40)
            entry.pack(side=tk.LEFT, padx=(5, 0))
            self.entries[key] = entry
        
        motivo_frame = tk.Frame(right_frame, bg="#34495e")
        motivo_frame.pack(fill=tk.X, pady=5)
        tk.Label(motivo_frame, text="Motivo:", anchor="nw", bg="#34495e", fg="white").pack(anchor="w")
        self.motivo_text = tk.Text(motivo_frame, height=4, font=("Arial", 11))
        self.motivo_text.pack(fill=tk.X, pady=(5, 0))
        
        salon_frame = tk.Frame(right_frame, bg="#34495e")
        salon_frame.pack(fill=tk.X, pady=(15,5))
        tk.Label(salon_frame, text="Seleccionar Salón:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        
        self.btn_polideportivo = tk.Button(salon_frame, text="Polideportivo", font=("Arial", 11), 
                                           command=lambda: self.seleccionar_salon("Polideportivo"),
                                           bg="#B0BEC5", fg="white", padx=15)
        self.btn_polideportivo.pack(side=tk.LEFT, padx=5)
        
        self.btn_sum = tk.Button(salon_frame, text="S.U.M.", font=("Arial", 11), 
                                 command=lambda: self.seleccionar_salon("S.U.M."),
                                 bg="#B0BEC5", fg="white", padx=15)
        self.btn_sum.pack(side=tk.LEFT, padx=5)
        
        status_frame = tk.Frame(right_frame, bg="#34495e")
        status_frame.pack(fill=tk.X, pady=(20,0))
        self.status_label = tk.Label(status_frame, text="", font=("Arial", 11, "bold"), bg="#34495e", fg="white")
        self.status_label.pack(pady=(0,10))
        
        btn_form_frame = tk.Frame(status_frame, bg="#34495e")
        btn_form_frame.pack()
        self.verificar_btn = tk.Button(btn_form_frame, text="Verificar", command=self.verificar_disponibilidad,
                                       bg="#FF9800", fg="white", padx=15, pady=5)
        self.verificar_btn.pack(side=tk.LEFT, padx=(0,10))
        self.guardar_btn = tk.Button(btn_form_frame, text="Guardar", command=self.guardar_reserva, state=tk.DISABLED,
                                     bg="#4CAF50", fg="white", padx=15, pady=5)
        self.guardar_btn.pack(side=tk.LEFT, padx=(0,10))
        tk.Button(btn_form_frame, text="Limpiar", command=self.limpiar_form, bg="#607D8B", fg="white", padx=15, pady=5).pack(side=tk.LEFT)

        tk.Button(btn_form_frame, text="Cerrar Aplicación", command=self.root.destroy, 
                  bg="#E74C3C", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=(10,0))
        
        tk.Button(btn_form_frame, text="Buscar Reservas", command=self.abrir_ventana_busqueda,
                  bg="#03A9F4", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=(10,0))

        tk.Button(btn_form_frame, text="Reservas Periódicas", command=self.abrir_ventana_periodica,
                  bg="#9C27B0", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=(10,0))
    
    def set_fecha_hoy(self):
        self.fecha_actual = date.today()
        self.fecha_entry.set_date(self.fecha_actual)
        self.actualizar_horarios()
    
    def on_fecha_change(self, event=None):
        self.fecha_actual = self.fecha_entry.get_date()
        self.actualizar_horarios()
        self.limpiar_form()
    
    def actualizar_horarios(self):
        if not self.salon_actual:
            return
        self.horarios_list.delete(0, tk.END)
        self.mapa_reservas_lista.clear()
        
        fecha_str = self.fecha_actual.strftime("%Y-%m-%d")
        reservas = self.db.get_reservas_dia(self.salon_actual, fecha_str)
        
        reservas_por_hora = {}
        for id_reserva, h_inicio, h_fin, solicitante in reservas:
            try:
                inicio_dt = datetime.strptime(h_inicio, "%H:%M")
                fin_dt = datetime.strptime(h_fin, "%H:%M")
                hora_actual = inicio_dt
                while hora_actual < fin_dt:
                    hora_str = hora_actual.strftime("%H:%M")
                    reservas_por_hora[hora_str] = {
                        "id": id_reserva,
                        "solicitante": solicitante
                    }
                    hora_actual += timedelta(hours=1)
            except ValueError:
                continue
        
        for hora in range(24):
            hora_str = f"{hora:02d}:00"
            if hora_str in reservas_por_hora:
                info = reservas_por_hora[hora_str]
                texto_item = f"{hora_str} - Ocupado - {info['solicitante']}"
                self.horarios_list.insert(tk.END, texto_item)
                self.horarios_list.itemconfig(tk.END, {'bg':'#FFEBEE', 'fg':'#B71C1C'})
                self.mapa_reservas_lista[texto_item] = info['id']
            else:
                texto_item = f"{hora_str}"
                self.horarios_list.insert(tk.END, texto_item)
                self.horarios_list.itemconfig(tk.END, {'bg':'#E8F5E9', 'fg':'#1B5E20'})
    
    def seleccionar_salon(self, salon):
        self.salon_actual = salon
        self.hora_inicio_seleccionada = None
        if salon == "Polideportivo":
            self.btn_polideportivo.config(bg="#4CAF50")
            self.btn_sum.config(bg="#B0BEC5")
        else:
            self.btn_sum.config(bg="#4CAF50")
            self.btn_polideportivo.config(bg="#B0BEC5")
        self.actualizar_horarios()
        self.limpiar_form()
    
    def on_horario_select(self, event):
        selection_idx = self.horarios_list.curselection()
        if not selection_idx:
            return
        item_texto = self.horarios_list.get(selection_idx[0])
        
        if "Ocupado" in item_texto:
            reserva_id = self.mapa_reservas_lista.get(item_texto)
            if reserva_id:
                self.show_reserva_details(reserva_id)
            self.hora_inicio_seleccionada = None
            self.limpiar_form_datos()
        else:
            hora = item_texto.strip()
            if self.hora_inicio_seleccionada is None:
                self.hora_inicio_seleccionada = hora
                self.entries["hora_inicio"].set(hora)
                self.entries["hora_fin"].set('')
                self.status_label.config(text="")
                self.guardar_btn.config(state=tk.DISABLED)
            else:
                hora_inicio = self.hora_inicio_seleccionada
                hora_fin = hora
                self.entries["hora_fin"].set(hora_fin)
                self.hora_inicio_seleccionada = None
                self.limpiar_form_datos()
    
    def show_context_menu(self, event):
        selection_idx = self.horarios_list.nearest(event.y)
        if selection_idx == -1:
            return
        self.horarios_list.selection_clear(0, tk.END)
        self.horarios_list.selection_set(selection_idx)
        item_texto = self.horarios_list.get(selection_idx)
        if "Ocupado" in item_texto:
            reserva_id = self.mapa_reservas_lista.get(item_texto)
            if reserva_id:
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Ver Detalles", command=lambda: self.show_reserva_details(reserva_id))
                menu.add_command(label="Eliminar Reserva", command=lambda: self.delete_reserva(reserva_id))
                menu.tk_popup(event.x_root, event.y_root)
    
    def show_reserva_details(self, reserva_id):
        details = self.db.get_reserva_details(reserva_id)
        if not details:
            messagebox.showerror("Error", "No se encontraron los detalles de la reserva.")
            return
        
        fecha_reserva_formato_local = datetime.strptime(details[2], '%Y-%m-%d').strftime('%d-%m-%y')
        fecha_creacion_formato_local = datetime.strptime(details[9], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%y %H:%M:%S')

        top = tk.Toplevel(self.root)
        top.title("Detalles de la Reserva")
        self.centrar_ventana(top, 550, 400)
        top.transient(self.root)
        top.configure(bg="#34495e")
        tk.Label(top, text="Detalles de la Reserva", font=("Arial", 14, "bold"), bg="#34495e", fg="white").pack(pady=10)
        info_text = tk.Text(top, height=15, width=60, font=("Arial", 11), wrap=tk.WORD, relief="flat", bg="#34495e", fg="white")
        info_text.pack(pady=10, padx=20)
        
        info_text.insert(tk.END, f"ID: {details[0]}\n")
        info_text.insert(tk.END, f"Salón: {details[1]}\n")
        info_text.insert(tk.END, f"Fecha: {fecha_reserva_formato_local}\n")
        info_text.insert(tk.END, f"Inicio: {details[3]}\n")
        info_text.insert(tk.END, f"Fin: {details[4]}\n")
        info_text.insert(tk.END, f"Solicitante: {details[5]}\n")
        info_text.insert(tk.END, f"Contacto: {details[6]}\n")
        info_text.insert(tk.END, f"Correo: {details[7]}\n")
        info_text.insert(tk.END, f"Motivo: {details[8]}\n")
        info_text.insert(tk.END, f"Fecha Creación: {fecha_creacion_formato_local}\n")

        info_text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(top, bg="#34495e")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Cerrar", command=top.destroy, bg="#607D8B", fg="white", padx=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Imprimir Ticket PDF", 
                  command=lambda: self.imprimir_pdf_reserva(details), 
                  bg="#FFC107", fg="white", padx=15).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Abrir Carpeta PDF", 
                  command=self.abrir_carpeta_pdf,
                  bg="#FF5722", fg="white", padx=15).pack(side=tk.LEFT, padx=5)


    def abrir_carpeta_pdf(self):
        pdf_path = "D:\\Sistema De Gestion De Reserva De Turnos\\PDF Reservas"
        if not os.path.exists(pdf_path):
            messagebox.showwarning("Advertencia", f"El directorio no existe: {pdf_path}")
            return
        try:
            os.startfile(pdf_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")

    def imprimir_pdf_reserva(self, details):
        pdf_path = "D:\\Sistema De Gestion De Reserva De Turnos\\PDF Reservas"
        
        if not os.path.exists(pdf_path):
            try:
                os.makedirs(pdf_path)
            except OSError as e:
                messagebox.showerror("Error de Directorio", f"No se pudo crear el directorio de destino: {e}")
                return

        id_reserva = details[0]
        fecha_creacion_nombre = datetime.strptime(details[9], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%y')
        solicitante = details[5]
        fecha_reserva_nombre = datetime.strptime(details[2], '%Y-%m-%d').strftime('%d-%m-%y')
        salon = details[1]
        
        nombre_archivo = f"{id_reserva} - {fecha_creacion_nombre} - {solicitante} - {fecha_reserva_nombre} - {salon}.pdf"
        ruta_completa = os.path.join(pdf_path, nombre_archivo)
        
        pdf = FPDF('P', 'mm', (80, 150))
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=5)
        pdf.set_font('Arial', '', 10)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 7, 'Ticket de Reserva', 0, 1, 'C')
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 5, 'Sistema de Reservas de Salones', 0, 1, 'C')
        pdf.ln(3)

        pdf.line(5, pdf.get_y(), 75, pdf.get_y())
        pdf.ln(3)

        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 5, f"ID: {details[0]}", 0, 1)
        pdf.cell(0, 5, f"Salón: {details[1]}", 0, 1)
        pdf.cell(0, 5, f"Fecha: {fecha_reserva_nombre}", 0, 1)
        pdf.cell(0, 5, f"Hora Inicio: {details[3]}", 0, 1)
        pdf.cell(0, 5, f"Hora Fin: {details[4]}", 0, 1)
        pdf.cell(0, 5, f"Solicitante: {details[5]}", 0, 1)
        pdf.cell(0, 5, f"Contacto: {details[6]}", 0, 1)
        pdf.cell(0, 5, f"Correo: {details[7]}", 0, 1)
        
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 5, 'Motivo:', 0, 1)
        pdf.set_font('Arial', '', 9)
        pdf.multi_cell(0, 4, details[8])
        
        pdf.ln(3)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 5, f'Creado: {datetime.strptime(details[9], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%y %H:%M:%S")}', 0, 1, 'L')
        pdf.cell(0, 5, f'Impreso: {datetime.now().strftime("%d-%m-%y %H:%M:%S")}', 0, 1, 'L')

        try:
            pdf.output(ruta_completa)
            os.startfile(ruta_completa)

        except Exception as e:
            messagebox.showerror("Error al guardar PDF", f"No se pudo guardar el archivo PDF: {e}")
    
    def delete_reserva(self, reserva_id):
        if messagebox.askyesno("Confirmar Eliminación", "¿Estás seguro de que quieres eliminar esta reserva?"):
            if self.db.delete_reserva(reserva_id):
                messagebox.showinfo("Éxito", "La reserva ha sido eliminada.")
                self.actualizar_horarios()
                self.limpiar_form()
            else:
                messagebox.showerror("Error", "No se pudo eliminar la reserva.")
    
    def verificar_disponibilidad(self):
        hora_inicio = self.entries["hora_inicio"].get().strip()
        hora_fin = self.entries["hora_fin"].get().strip()
        if not hora_inicio or not hora_fin:
            messagebox.showwarning("Advertencia", "Ingrese hora de inicio y fin")
            return
        try:
            inicio_dt = datetime.strptime(hora_inicio, "%H:%M")
            fin_dt = datetime.strptime(hora_fin, "%H:%M")
        except ValueError:
            messagebox.showerror("Error", "Formato de hora inválido. Use HH:MM")
            return
        fecha_str = self.fecha_actual.strftime("%Y-%m-%d")
        disponible = self.db.verificar_disponibilidad(self.salon_actual, fecha_str, hora_inicio, hora_fin)
        if disponible:
            self.status_label.config(text="✅ HORARIO DISPONIBLE", fg="#2ECC71")
            self.guardar_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="❌ HORARIO OCUPADO", fg="#E74C3C")
            self.guardar_btn.config(state=tk.DISABLED)
    
    def guardar_reserva(self):
        campos_requeridos = {"solicitante", "contacto", "correo"}
        for campo in campos_requeridos:
            if not self.entries[campo].get().strip():
                messagebox.showwarning("Advertencia", f"El campo {campo.title()} es obligatorio")
                return
        motivo = self.motivo_text.get("1.0", tk.END).strip()
        if not motivo:
            messagebox.showwarning("Advertencia", "El motivo es obligatorio")
            return

        hora_inicio = self.entries["hora_inicio"].get().strip()
        hora_fin = self.entries["hora_fin"].get().strip()
        
        if not self.db.verificar_disponibilidad(self.salon_actual, self.fecha_actual.strftime("%Y-%m-%d"), hora_inicio, hora_fin):
            messagebox.showerror("Error", "El horario ya no está disponible. Verifique de nuevo.")
            return

        reserva_id = self.db.guardar_reserva(
            self.salon_actual,
            self.fecha_actual.strftime("%Y-%m-%d"),
            hora_inicio,
            hora_fin,
            self.entries["solicitante"].get().strip(),
            self.entries["contacto"].get().strip(),
            self.entries["correo"].get().strip(),
            motivo
        )

        if reserva_id:
            reserva_details = self.db.get_reserva_details(reserva_id)
            if reserva_details:
                self.imprimir_pdf_reserva(reserva_details)
                self.show_reserva_details(reserva_id)
                self.limpiar_form()
                self.actualizar_horarios()
        else:
            messagebox.showerror("Error", "No se pudo guardar la reserva.")
    
    def limpiar_form_datos(self):
        for key in ["solicitante", "contacto", "correo"]:
            self.entries[key].delete(0, tk.END)
        self.motivo_text.delete("1.0", tk.END)
        self.status_label.config(text="")
        self.guardar_btn.config(state=tk.DISABLED)
    
    def limpiar_form(self):
        for key, entry in self.entries.items():
            if isinstance(entry, ttk.Combobox):
                entry.set('')
            else:
                entry.delete(0, tk.END)
        self.motivo_text.delete("1.0", tk.END)
        self.status_label.config(text="")
        self.guardar_btn.config(state=tk.DISABLED)
        self.hora_inicio_seleccionada = None
    
    def run(self):
        self.root.mainloop()

    # ===== Funcionalidad de Búsqueda =====
    def abrir_ventana_busqueda(self):
        self.ventana_busqueda = tk.Toplevel(self.root)
        self.ventana_busqueda.title("Buscar y Filtrar Reservas")
        self.ventana_busqueda.state('zoomed')
        self.ventana_busqueda.configure(bg="#2c3e50")
        
        busqueda_frame = tk.LabelFrame(self.ventana_busqueda, text="Filtros de Búsqueda", 
                                       font=("Arial", 12, "bold"), bg="#34495e", fg="white", 
                                       padx=15, pady=15)
        busqueda_frame.pack(fill=tk.X, padx=20, pady=10)

        filtro_campos = tk.Frame(busqueda_frame, bg="#34495e")
        filtro_campos.pack(fill=tk.X)

        tk.Label(filtro_campos, text="ID Reserva:", bg="#34495e", fg="white").pack(side=tk.LEFT, padx=5)
        self.entry_id = tk.Entry(filtro_campos, width=8, font=("Arial", 11))
        self.entry_id.pack(side=tk.LEFT, padx=5)
        self.entry_id.bind('<KeyRelease>', lambda e: self.ejecutar_busqueda())
        
        tk.Label(filtro_campos, text="Solicitante:", bg="#34495e", fg="white").pack(side=tk.LEFT, padx=5)
        self.entry_solicitante = tk.Entry(filtro_campos, width=20, font=("Arial", 11))
        self.entry_solicitante.pack(side=tk.LEFT, padx=5)
        self.entry_solicitante.bind('<KeyRelease>', lambda e: self.ejecutar_busqueda())

        tk.Label(filtro_campos, text="Salón:", bg="#34495e", fg="white").pack(side=tk.LEFT, padx=5)
        self.combo_salon = ttk.Combobox(filtro_campos, values=["", "Polideportivo", "S.U.M."], font=("Arial", 11), width=15)
        self.combo_salon.pack(side=tk.LEFT, padx=5)
        self.combo_salon.bind('<<ComboboxSelected>>', lambda e: self.ejecutar_busqueda())

        tk.Label(filtro_campos, text="Fecha:", bg="#34495e", fg="white").pack(side=tk.LEFT, padx=5)
        self.entry_fecha_busqueda = DateEntry(filtro_campos, width=12, date_pattern='y-mm-dd',
                                                background='darkblue', foreground='white', borderwidth=2)
        self.entry_fecha_busqueda.pack(side=tk.LEFT, padx=5)
        self.entry_fecha_busqueda.bind('<<DateEntrySelected>>', lambda e: self.ejecutar_busqueda())

        self.check_todas_fechas_var = tk.IntVar(value=1)
        self.check_todas_fechas = tk.Checkbutton(filtro_campos, text="Todas las Fechas", 
                                                 variable=self.check_todas_fechas_var, 
                                                 bg="#34495e", fg="white", selectcolor="#2c3e50",
                                                 command=self.toggle_fecha_busqueda)
        self.check_todas_fechas.pack(side=tk.LEFT, padx=(10, 5))

        btn_frame_busqueda = tk.Frame(busqueda_frame, bg="#34495e")
        btn_frame_busqueda.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame_busqueda, text="Buscar", command=self.ejecutar_busqueda, bg="#03A9F4", fg="white", padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame_busqueda, text="Limpiar Filtros", command=self.limpiar_filtros_busqueda, bg="#607D8B", fg="white", padx=15).pack(side=tk.LEFT, padx=5)

        tree_frame = tk.Frame(self.ventana_busqueda, bg="#34495e")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("ID", "Salón", "Fecha", "Hora Inicio", "Hora Fin", "Solicitante")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scrollbar_y.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set)

        self.tree.bind('<Double-Button-1>', self.on_reserva_double_click)
        self.ejecutar_busqueda()

    def toggle_fecha_busqueda(self):
        if self.check_todas_fechas_var.get() == 1:
            self.entry_fecha_busqueda.config(state="disabled")
        else:
            self.entry_fecha_busqueda.config(state="normal")
        self.ejecutar_busqueda()

    def limpiar_filtros_busqueda(self):
        self.entry_id.delete(0, tk.END)
        self.entry_solicitante.delete(0, tk.END)
        self.combo_salon.set("")
        self.check_todas_fechas_var.set(1)
        self.entry_fecha_busqueda.config(state="disabled")
        self.ejecutar_busqueda()

    def ejecutar_busqueda(self):
        id_reserva = self.entry_id.get().strip()
        solicitante = self.entry_solicitante.get().strip()
        salon = self.combo_salon.get().strip()
        fecha = self.entry_fecha_busqueda.get().strip() if self.check_todas_fechas_var.get() == 0 else ""
        
        if id_reserva:
            resultados = self.db.search_reservas(id_reserva=id_reserva)
        else:
            resultados = self.db.search_reservas(solicitante=solicitante, salon=salon, fecha=fecha)
        
        self.tree.delete(*self.tree.get_children())
        for row in resultados:
            reserva_id, salon, fecha, hora_inicio, hora_fin, solicitante, _, _, _, _ = row
            fecha_formateada = datetime.strptime(fecha, '%Y-%m-%d').strftime('%d-%m-%y')
            self.tree.insert("", "end", values=(reserva_id, salon, fecha_formateada, hora_inicio, hora_fin, solicitante), iid=reserva_id)

    def on_reserva_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id:
            return
        reserva_id = self.tree.item(item_id, 'values')[0]
        self.show_reserva_details(reserva_id)

    def abrir_ventana_periodica(self):
        ReservasPeriodicasWindow(self.root, self.db, self.actualizar_horarios)

# --- INICIO DE LA CLASE DE LA NUEVA VENTANA ---

class ReservasPeriodicasWindow:
    def __init__(self, parent, db, on_close_callback):
        self.parent = parent
        self.db = db
        self.on_close_callback = on_close_callback

        self.top = tk.Toplevel(parent)
        self.top.title("Reservas Periódicas (Lote)")
        self.top.transient(parent)

        # Aumento del ancho en 20%
        self.width = 780
        self.height = 500
        x = (self.top.winfo_screenwidth() // 2) - (self.width // 2)
        y = (self.top.winfo_screenheight() // 2) - (self.height // 2)
        self.top.geometry(f'{self.width}x{self.height}+{x}+{y}')
        
        self.top.configure(bg="#2c3e50")
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_gui()
    
    def on_closing(self):
        self.on_close_callback()
        self.top.destroy()

    def setup_gui(self):
        main_frame = tk.LabelFrame(self.top, text="Generar Reservas por Lote", font=("Arial", 12, "bold"), 
                                    bg="#34495e", fg="white", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        campos_frame = tk.Frame(main_frame, bg="#34495e")
        campos_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.entries = {}
        horas_disponibles = [f"{h:02d}:00" for h in range(24)]

        # Ajuste de anchos para los campos
        data_fields = [
            ("Salón:", "salon", ["", "Polideportivo", "S.U.M."], 20),
            ("Hora Inicio:", "hora_inicio", horas_disponibles, 20),
            ("Hora Fin:", "hora_fin", horas_disponibles, 20),
            ("Solicitante:", "solicitante", None, 80),
            ("Contacto:", "contacto", None, 80),
            ("Correo:", "correo", None, 80)
        ]
        
        for i, (label_text, key, values, width) in enumerate(data_fields):
            row_frame = tk.Frame(campos_frame, bg="#34495e")
            row_frame.pack(fill=tk.X, pady=3)
            tk.Label(row_frame, text=label_text, width=12, anchor="w", bg="#34495e", fg="white").pack(side=tk.LEFT)
            if values:
                entry = ttk.Combobox(row_frame, values=values, font=("Arial", 11), state="readonly", width=width)
                if key == "salon":
                    entry.set("")
            else:
                entry = tk.Entry(row_frame, font=("Arial", 11), width=width)
            # Modificación clave: no usar expand=True para que los campos no se estiren
            entry.pack(side=tk.LEFT, padx=(5, 0)) 
            self.entries[key] = entry
            
        motivo_frame = tk.Frame(campos_frame, bg="#34495e")
        motivo_frame.pack(fill=tk.X, pady=5)
        tk.Label(motivo_frame, text="Motivo:", anchor="w", bg="#34495e", fg="white").pack(anchor="w")
        self.motivo_text = tk.Text(motivo_frame, height=4, font=("Arial", 11))
        # También se elimina la expansión del campo de motivo para que mantenga su tamaño
        self.motivo_text.pack(fill=tk.X, expand=False) 

        periodicidad_frame = tk.LabelFrame(main_frame, text="Periodicidad (Resto del mes)", font=("Arial", 11, "bold"), 
                                            bg="#34495e", fg="white", padx=10, pady=5)
        periodicidad_frame.pack(fill=tk.X, pady=10)
        
        dias_frame = tk.Frame(periodicidad_frame, bg="#34495e")
        dias_frame.pack(fill=tk.X)
        tk.Label(dias_frame, text="Días de la semana:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        
        self.dias_semana_vars = {}
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        dias_contenedor = tk.Frame(dias_frame, bg="#34495e")
        dias_contenedor.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for i, dia in enumerate(dias):
            self.dias_semana_vars[i] = tk.IntVar()
            chk = tk.Checkbutton(dias_contenedor, text=dia, variable=self.dias_semana_vars[i], 
                                 bg="#34495e", fg="white", selectcolor="#2c3e50")
            chk.pack(side=tk.LEFT, padx=3)

        btn_frame = tk.Frame(main_frame, bg="#34495e")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Generar Reservas", command=self.generar_reservas,
                  bg="#4CAF50", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Limpiar", command=self.limpiar_form,
                  bg="#607D8B", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cerrar", command=self.on_closing,
                  bg="#E74C3C", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def generar_reservas(self):
        salon = self.entries["salon"].get().strip()
        hora_inicio = self.entries["hora_inicio"].get().strip()
        hora_fin = self.entries["hora_fin"].get().strip()
        solicitante = self.entries["solicitante"].get().strip()
        motivo = self.motivo_text.get("1.0", tk.END).strip()
        contacto = self.entries["contacto"].get().strip()
        correo = self.entries["correo"].get().strip()

        if not all([salon, hora_inicio, hora_fin, solicitante, motivo]):
            messagebox.showwarning("Advertencia", "Todos los campos de reserva son obligatorios.")
            return

        dias_seleccionados = [i for i, var in self.dias_semana_vars.items() if var.get() == 1]
        if not dias_seleccionados:
            messagebox.showwarning("Advertencia", "Seleccione al menos un día de la semana.")
            return

        hoy = date.today()
        proximo_mes = hoy.replace(day=28) + timedelta(days=4)
        ultimo_dia_mes = proximo_mes - timedelta(days=proximo_mes.day)

        fecha_actual = hoy
        reservas_creadas = 0
        conflictos = []

        while fecha_actual <= ultimo_dia_mes:
            if fecha_actual.weekday() in dias_seleccionados:
                fecha_str = fecha_actual.strftime("%Y-%m-%d")
                if self.db.verificar_disponibilidad(salon, fecha_str, hora_inicio, hora_fin):
                    self.db.guardar_reserva(
                        salon, fecha_str, hora_inicio, hora_fin, solicitante, contacto, correo, motivo
                    )
                    reservas_creadas += 1
                else:
                    conflictos.append(fecha_actual.strftime("%d-%m-%Y"))
            
            fecha_actual += timedelta(days=1)

        mensaje = f"Proceso de reservas periódicas finalizado.\n"
        mensaje += f"Reservas creadas: {reservas_creadas}\n"
        if conflictos:
            mensaje += f"Conflictos encontrados ({len(conflictos)}):\n"
            mensaje += ", ".join(conflictos)
            messagebox.showwarning("Proceso con Conflictos", mensaje)
        else:
            messagebox.showinfo("Proceso Exitoso", mensaje)
            
        self.limpiar_form()
        self.on_closing()

    def limpiar_form(self):
        for key in self.entries:
            if isinstance(self.entries[key], ttk.Combobox):
                self.entries[key].set('')
            else:
                self.entries[key].delete(0, tk.END)
        self.motivo_text.delete("1.0", tk.END)
        for var in self.dias_semana_vars.values():
            var.set(0)

if __name__ == "__main__":
    app = SistemaReservas()
    app.run()