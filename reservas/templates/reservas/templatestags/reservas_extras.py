from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permite acceder a items de diccionario en templates"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def mul(value, arg):
    """Multiplica dos valores"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide dos valores"""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0 {{ vuelo.fecha_salida|date:"d/m/Y H:i" }}</p>
                                    <p><strong>Llegada:</strong> {{ vuelo.fecha_llegada|date:"d/m/Y H:i" }}</p>
                                </div>
                            </div>
                            
                            <!-- Escalas si existen -->
                            {% if vuelo.tiene_escalas and vuelo.escalas %}
                                <hr>
                                <h6>🔄 Escalas</h6>
                                {% for escala in vuelo.escalas %}
                                    <div class="card">
                                        <div class="card-body py-2">
                                            <h6 class="card-title">Escala {{ escala.orden }}</h6>
                                            <div class="row">
                                                <div class="col-md-6">
                                                    <small>
                                                        <strong>Ruta:</strong> {{ escala.origen }} → {{ escala.destino }}<br>
                                                        <strong>Avión:</strong> {{ escala.avion }}
                                                    </small>
                                                </div>
                                                <div class="col-md-6">
                                                    <small>
                                                        <strong>Salida:</strong> {{ escala.fecha_salida|date:"d/m/Y H:i" }}<br>
                                                        <strong>Llegada:</strong> {{ escala.fecha_llegada|date:"d/m/Y H:i" }}
                                                    </small>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                    </div>
                </div>

                <!-- Asientos -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5>🪑 Asientos Asignados</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Asiento</th>
                                        <th>Tipo</th>
                                        <th>Precio</th>
                                        <th>Avión</th>
                                        <th>Escala</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for asiento in boleto.asientos_data %}
                                        <tr>
                                            <td><strong>{{ asiento.numero }}</strong></td>
                                            <td>{{ asiento.tipo }}</td>
                                            <td>${{ asiento.precio }}</td>
                                            <td>{{ asiento.avion }}</td>
                                            <td>
                                                {% if asiento.escala %}
                                                    Escala {{ asiento.escala.orden }}: {{ asiento.escala.origen }} → {{ asiento.escala.destino }}
                                                {% else %}
                                                    Vuelo Principal
                                                {% endif %}
                                            </td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <!-- Acciones -->
                <div class="card">
                    <div class="card-header">
                        <h5>📋 Acciones</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="{% url 'reservas:descargar_boleto' boleto.pk %}" 
                               class="btn btn-primary">
                                📥 Descargar PDF
                            </a>
                            
                            {% if not es_admin %}
                                <a href="{% url 'reservas:mis_reservas' %}" 
                                   class="btn btn-outline-primary">
                                    📋 Mis Reservas
                                </a>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <!-- Información importante -->
                <div class="card mt-3">
                    <div class="card-header bg-info text-white">
                        <h6>ℹ️ Información Importante</h6>
                    </div>
                    <div class="card-body">
                        <ul class="small mb-0">
                            <li>Preséntese 2 horas antes del vuelo</li>
                            <li>Porte documento de identidad válido</li>
                            <li>Revise restricciones de equipaje</li>
                            <li>Este boleto es válido solo para las fechas indicadas</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
