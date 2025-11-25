from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.metrics import dp

from planificador import Planificador
from proceso import Proceso

class ProcesoInput(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 5
        self.size_hint_y = None
        self.height = dp(40)
        
        self.pid_input = TextInput(hint_text='PID', multiline=False, size_hint_x=0.2)
        self.llegada_input = TextInput(hint_text='Llegada', multiline=False, size_hint_x=0.2)
        self.cpu_input = TextInput(hint_text='CPU', multiline=False, size_hint_x=0.2)
        self.memoria_input = TextInput(hint_text='Memoria', multiline=False, size_hint_x=0.2)
        self.prioridad_input = TextInput(hint_text='Prioridad', multiline=False, size_hint_x=0.2)
        
        self.add_widget(self.pid_input)
        self.add_widget(self.llegada_input)
        self.add_widget(self.cpu_input)
        self.add_widget(self.memoria_input)
        self.add_widget(self.prioridad_input)
    
    def obtener_datos(self):
        try:
            return {
                'pid': int(self.pid_input.text),
                'llegada': int(self.llegada_input.text),
                'cpu': int(self.cpu_input.text),
                'memoria': int(self.memoria_input.text) if self.memoria_input.text else 0,
                'prioridad': int(self.prioridad_input.text) if self.prioridad_input.text else 0
            }
        except ValueError:
            return None

class GanttChart(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(100)
        self.bind(size=self._update_rect)
        
        self.title = Label(text='Diagrama de Gantt', size_hint_y=None, height=dp(30))
        self.add_widget(self.title)
        
        self.chart_container = BoxLayout(size_hint_y=None, height=dp(70))
        self.add_widget(self.chart_container)
        
        with self.canvas.before:
            Color(0.9, 0.9, 0.9, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
    
    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos
    
    def actualizar_gantt(self, gantt_data):
        self.chart_container.clear_widgets()
        
        if not gantt_data:
            return
        
        # Encontrar tiempo máximo
        tiempo_max = max([t[0] for t in gantt_data]) + 1 if gantt_data else 1
        
        # Crear escala de tiempo
        escala = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
        for i in range(0, tiempo_max + 1, max(1, tiempo_max // 10)):
            label = Label(text=str(i), size_hint_x=None, width=dp(30))
            escala.add_widget(label)
        self.chart_container.add_widget(escala)
        
        # Crear barras de procesos
        barras = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        procesos_vistos = set()
        for tiempo, pid in gantt_data:
            if pid not in procesos_vistos:
                barra = Label(text=f'P{pid}', size_hint_x=None, width=dp(40))
                barras.add_widget(barra)
                procesos_vistos.add(pid)
        
        self.chart_container.add_widget(barras)

class PlanificadorApp(App):
    def build(self):
        self.planificador = Planificador()
        self.simulando = False
        self.evento_simulacion = None
        
        # Layout principal
        layout_principal = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Título
        titulo = Label(text='Sistema de Planificación de Procesos', size_hint_y=None, height=dp(40),
                      font_size='20sp', bold=True)
        layout_principal.add_widget(titulo)
        
        # Sección de entrada de datos
        seccion_entrada = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200))
        
        # Controles de algoritmo
        controles_algoritmo = BoxLayout(size_hint_y=None, height=dp(40))
        controles_algoritmo.add_widget(Label(text='Algoritmo:', size_hint_x=0.3))
        
        self.spinner_algoritmo = Spinner(
            text='FCFS',
            values=('FCFS', 'SJF', 'SRTF', 'Round Robin', 'Prioridades No Apropiativo', 'Prioridades Apropiativo'),
            size_hint_x=0.4
        )
        self.spinner_algoritmo.bind(text=self.on_algoritmo_change)
        controles_algoritmo.add_widget(self.spinner_algoritmo)
        
        controles_algoritmo.add_widget(Label(text='Quantum:', size_hint_x=0.2))
        self.quantum_input = TextInput(text='2', multiline=False, size_hint_x=0.2)
        controles_algoritmo.add_widget(self.quantum_input)
        
        seccion_entrada.add_widget(controles_algoritmo)
        
        # Entrada de proceso
        self.entrada_proceso = ProcesoInput()
        seccion_entrada.add_widget(self.entrada_proceso)
        
        # Botones de control
        botones_control = BoxLayout(size_hint_y=None, height=dp(40))
        self.btn_agregar = Button(text='Agregar Proceso')
        self.btn_agregar.bind(on_press=self.agregar_proceso)
        
        self.btn_iniciar = Button(text='Iniciar Simulación')
        self.btn_iniciar.bind(on_press=self.iniciar_simulacion)
        
        self.btn_pausar = Button(text='Pausar')
        self.btn_pausar.bind(on_press=self.pausar_simulacion)
        
        self.btn_reiniciar = Button(text='Reiniciar')
        self.btn_reiniciar.bind(on_press=self.reiniciar_simulacion)
        
        self.btn_limpiar = Button(text='Limpiar Todo')
        self.btn_limpiar.bind(on_press=self.limpiar_todo)
        
        botones_control.add_widget(self.btn_agregar)
        botones_control.add_widget(self.btn_iniciar)
        botones_control.add_widget(self.btn_pausar)
        botones_control.add_widget(self.btn_reiniciar)
        botones_control.add_widget(self.btn_limpiar)
        
        seccion_entrada.add_widget(botones_control)
        
        layout_principal.add_widget(seccion_entrada)
        
        # Sección de visualización
        seccion_visualizacion = BoxLayout(orientation='horizontal', spacing=10)
        
        # Columna izquierda - Lista de procesos
        columna_izquierda = BoxLayout(orientation='vertical', size_hint_x=0.4)
        
        columna_izquierda.add_widget(Label(text='Procesos Ingresados', size_hint_y=None, height=dp(30)))
        
        self.lista_procesos = GridLayout(cols=6, size_hint_y=None)
        self.lista_procesos.add_widget(Label(text='PID', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Llegada', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='CPU', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Memoria', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Prioridad', size_hint_x=0.2))
        self.lista_procesos.add_widget(Label(text='Estado', size_hint_x=0.2))
        self.lista_procesos.height = dp(40)
        
        scroll_lista = ScrollView()
        scroll_lista.add_widget(self.lista_procesos)
        columna_izquierda.add_widget(scroll_lista)
        
        # Diagrama de Gantt
        self.gantt_chart = GanttChart()
        columna_izquierda.add_widget(self.gantt_chart)
        
        seccion_visualizacion.add_widget(columna_izquierda)
        
        # Columna derecha - Estado del sistema
        columna_derecha = BoxLayout(orientation='vertical', size_hint_x=0.6)
        
        # Información en tiempo real
        info_tiempo_real = GridLayout(cols=2, size_hint_y=None, height=dp(100))
        info_tiempo_real.add_widget(Label(text='Tiempo Actual:'))
        self.label_tiempo = Label(text='0')
        info_tiempo_real.add_widget(self.label_tiempo)
        
        info_tiempo_real.add_widget(Label(text='Proceso Ejecutando:'))
        self.label_ejecutando = Label(text='Ninguno')
        info_tiempo_real.add_widget(self.label_ejecutando)
        
        columna_derecha.add_widget(info_tiempo_real)
        
        # Colas del sistema
        colas_sistema = GridLayout(cols=3, spacing=10)
        
        # Cola Ready
        cola_ready = BoxLayout(orientation='vertical')
        cola_ready.add_widget(Label(text='Cola Ready', size_hint_y=None, height=dp(30)))
        self.lista_ready = Label(text='Vacía', size_hint_y=1)
        scroll_ready = ScrollView()
        scroll_ready.add_widget(self.lista_ready)
        cola_ready.add_widget(scroll_ready)
        colas_sistema.add_widget(cola_ready)
        
        # Cola Espera
        cola_espera = BoxLayout(orientation='vertical')
        cola_espera.add_widget(Label(text='Cola Espera', size_hint_y=None, height=dp(30)))
        self.lista_espera = Label(text='Vacía', size_hint_y=1)
        scroll_espera = ScrollView()
        scroll_espera.add_widget(self.lista_espera)
        cola_espera.add_widget(scroll_espera)
        colas_sistema.add_widget(cola_espera)
        
        # Procesos Terminados
        cola_terminados = BoxLayout(orientation='vertical')
        cola_terminados.add_widget(Label(text='Terminados', size_hint_y=None, height=dp(30)))
        self.lista_terminados = Label(text='Vacía', size_hint_y=1)
        scroll_terminados = ScrollView()
        scroll_terminados.add_widget(self.lista_terminados)
        cola_terminados.add_widget(scroll_terminados)
        colas_sistema.add_widget(cola_terminados)
        
        columna_derecha.add_widget(colas_sistema)
        
        # Estadísticas
        estadisticas = GridLayout(cols=2, size_hint_y=None, height=dp(100))
        estadisticas.add_widget(Label(text='Tiempo Espera Promedio:'))
        self.label_espera_prom = Label(text='0')
        estadisticas.add_widget(self.label_espera_prom)
        
        estadisticas.add_widget(Label(text='Tiempo Retorno Promedio:'))
        self.label_retorno_prom = Label(text='0')
        estadisticas.add_widget(self.label_retorno_prom)
        
        estadisticas.add_widget(Label(text='Tiempo Respuesta Promedio:'))
        self.label_respuesta_prom = Label(text='0')
        estadisticas.add_widget(self.label_respuesta_prom)
        
        estadisticas.add_widget(Label(text='Uso de CPU:'))
        self.label_uso_cpu = Label(text='0%')
        estadisticas.add_widget(self.label_uso_cpu)
        
        columna_derecha.add_widget(estadisticas)
        
        seccion_visualizacion.add_widget(columna_derecha)
        layout_principal.add_widget(seccion_visualizacion)
        
        return layout_principal
    
    def on_algoritmo_change(self, spinner, text):
        self.planificador.algoritmo = text
    
    def agregar_proceso(self, instance):
        datos = self.entrada_proceso.obtener_datos()
        if datos is None:
            self.mostrar_error("Datos inválidos. Verifique que todos los campos sean números enteros.")
            return
        
        # Verificar si el PID ya existe
        for proceso in self.planificador.procesos:
            if proceso.pid == datos['pid']:
                self.mostrar_error(f"El PID {datos['pid']} ya existe.")
                return
        
        proceso = Proceso(
            datos['pid'], datos['llegada'], datos['cpu'],
            datos['memoria'], datos['prioridad']
        )
        self.planificador.agregar_proceso(proceso)
        self.actualizar_lista_procesos()
        
        # Limpiar campos de entrada
        self.entrada_proceso.pid_input.text = ''
        self.entrada_proceso.llegada_input.text = ''
        self.entrada_proceso.cpu_input.text = ''
        self.entrada_proceso.memoria_input.text = ''
        self.entrada_proceso.prioridad_input.text = ''
    
    def actualizar_lista_procesos(self):
        self.lista_procesos.clear_widgets()
        
        # Encabezados
        self.lista_procesos.add_widget(Label(text='PID', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Llegada', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='CPU', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Memoria', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Prioridad', size_hint_x=0.2))
        self.lista_procesos.add_widget(Label(text='Estado', size_hint_x=0.2))
        
        for proceso in self.planificador.procesos:
            self.lista_procesos.add_widget(Label(text=str(proceso.pid), size_hint_x=0.15))
            self.lista_procesos.add_widget(Label(text=str(proceso.tiempo_llegada), size_hint_x=0.15))
            self.lista_procesos.add_widget(Label(text=str(proceso.tiempo_cpu), size_hint_x=0.15))
            self.lista_procesos.add_widget(Label(text=str(proceso.tiempo_memoria), size_hint_x=0.15))
            self.lista_procesos.add_widget(Label(text=str(proceso.prioridad), size_hint_x=0.2))
            self.lista_procesos.add_widget(Label(text=proceso.estado, size_hint_x=0.2))
        
        self.lista_procesos.height = dp(40 + len(self.planificador.procesos) * 30)
    
    def iniciar_simulacion(self, instance):
        if not self.planificador.procesos:
            self.mostrar_error("No hay procesos para simular.")
            return
        
        try:
            if self.spinner_algoritmo.text == "Round Robin":
                self.planificador.quantum = int(self.quantum_input.text)
        except ValueError:
            self.mostrar_error("Quantum debe ser un número entero.")
            return
        
        self.planificador.algoritmo = self.spinner_algoritmo.text
        self.planificador.inicializar_simulacion()
        self.simulando = True
        
        # Programar la simulación paso a paso
        self.evento_simulacion = Clock.schedule_interval(self.ejecutar_paso_simulacion, 1.0)
    
    def ejecutar_paso_simulacion(self, dt):
        if self.simulando:
            estado_antes = len(self.planificador.procesos_terminados)
            self.planificador.ejecutar_paso()
            estado_despues = len(self.planificador.procesos_terminados)
            
            self.actualizar_interfaz()
            
            # Si terminó la simulación
            if estado_despues == len(self.planificador.procesos):
                self.simulando = False
                if self.evento_simulacion:
                    self.evento_simulacion.cancel()
                self.mostrar_estadisticas_finales()
    
    def pausar_simulacion(self, instance):
        self.simulando = False
        if self.evento_simulacion:
            self.evento_simulacion.cancel()
    
    def reiniciar_simulacion(self, instance):
        self.simulando = False
        if self.evento_simulacion:
            self.evento_simulacion.cancel()
        
        # Mantener los procesos pero reiniciar la simulación
        for proceso in self.planificador.procesos:
            proceso.estado = "Nuevo"
            proceso.tiempo_restante = proceso.tiempo_cpu
            proceso.tiempo_espera = 0
            proceso.tiempo_respuesta = -1
        
        self.planificador.tiempo_actual = 0
        self.planificador.proceso_ejecutando = None
        self.planificador.cola_ready.clear()
        self.planificador.cola_espera.clear()
        self.planificador.procesos_terminados.clear()
        self.planificador.gantt.clear()
        
        self.actualizar_interfaz()
    
    def limpiar_todo(self, instance):
        self.simulando = False
        if self.evento_simulacion:
            self.evento_simulacion.cancel()
        
        self.planificador.reset()
        self.actualizar_interfaz()
    
    def actualizar_interfaz(self):
        # Actualizar tiempo actual
        self.label_tiempo.text = str(self.planificador.tiempo_actual)
        
        # Actualizar proceso ejecutando
        if self.planificador.proceso_ejecutando:
            self.label_ejecutando.text = f"P{self.planificador.proceso_ejecutando.pid}"
        else:
            self.label_ejecutando.text = "Ninguno"
        
        # Actualizar colas
        self.lista_ready.text = "\n".join([f"P{p.pid} (CPU:{p.tiempo_restante})" 
                                          for p in self.planificador.cola_ready])
        self.lista_espera.text = "\n".join([f"P{p.pid}" for p in self.planificador.cola_espera])
        self.lista_terminados.text = "\n".join([f"P{p.pid} (Fin:{p.tiempo_fin})" 
                                               for p in self.planificador.procesos_terminados])
        
        # Actualizar diagrama de Gantt
        self.gantt_chart.actualizar_gantt(self.planificador.gantt)
        
        # Actualizar lista de procesos
        self.actualizar_lista_procesos()
        
        # Actualizar estadísticas si están disponibles
        if self.planificador.estadisticas:
            stats = self.planificador.estadisticas
            self.label_espera_prom.text = f"{stats['promedio_espera']:.2f}"
            self.label_retorno_prom.text = f"{stats['promedio_retorno']:.2f}"
            self.label_respuesta_prom.text = f"{stats['promedio_respuesta']:.2f}"
            self.label_uso_cpu.text = f"{stats['uso_cpu']*100:.1f}%"
    
    def mostrar_error(self, mensaje):
        popup = Popup(title='Error',
                     content=Label(text=mensaje),
                     size_hint=(0.6, 0.3))
        popup.open()
    
    def mostrar_estadisticas_finales(self):
        if not self.planificador.estadisticas:
            self.planificador.calcular_estadisticas()
        
        stats = self.planificador.estadisticas
        
        contenido = BoxLayout(orientation='vertical', spacing=10)
        contenido.add_widget(Label(text=f"Procesos ejecutados: {stats['total_procesos']}"))
        contenido.add_widget(Label(text=f"Tiempo espera promedio: {stats['promedio_espera']:.2f}"))
        contenido.add_widget(Label(text=f"Tiempo retorno promedio: {stats['promedio_retorno']:.2f}"))
        contenido.add_widget(Label(text=f"Tiempo respuesta promedio: {stats['promedio_respuesta']:.2f}"))
        contenido.add_widget(Label(text=f"Uso de CPU: {stats['uso_cpu']*100:.1f}%"))
        
        btn_cerrar = Button(text='Cerrar', size_hint_y=None, height=dp(40))
        popup = Popup(title='Estadísticas Finales', content=contenido, size_hint=(0.7, 0.5))
        btn_cerrar.bind(on_press=popup.dismiss)
        contenido.add_widget(btn_cerrar)
        
        popup.open()

if __name__ == '__main__':
    PlanificadorApp().run()