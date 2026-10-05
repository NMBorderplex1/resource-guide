import json, re, sys, copy
sys.stdout.reconfigure(encoding='utf-8')

BASE = json.load(open('data/widget_data_en.json', encoding='utf-8'))      # English + locations
PDF_EN = json.load(open('data/en_pdf.json', encoding='utf-8'))       # aligned with PDF_ES
PDF_ES = json.load(open('data/es_pdf.json', encoding='utf-8'))

IND_ES = [  # same order as the 25 Industry-Specific Incentives in the widget
 'Deducción fiscal por reacondicionamiento o remodelación de aeronaves',
 'Deducción fiscal por investigación y desarrollo aeroespacial',
 'Deducción fiscal por fabricación de aeronaves',
 'Deducción de GRT para actividades espaciales',
 'Deducciones y exenciones fiscales para negocios agrícolas',
 'Tasa fiscal preferencial para productores de cerveza y vino',
 'Créditos fiscales por energía avanzada',
 'Crédito fiscal para fabricantes de productos de energía alternativa',
 'Exención de GRT para sistemas de energía solar',
 'Crédito al impuesto sobre la renta por desarrollo del mercado solar',
 'Crédito fiscal por construcción sostenible',
 'Exención fiscal para vehículos híbridos',
 'Crédito fiscal y deducción de GRT por generación de electricidad geotérmica',
 'Deducción por equipo y materiales de biomasa',
 'Crédito fiscal para producciones cinematográficas (25% base, hasta 40% con bonificaciones)',
 'Programa de préstamos para inversión cinematográfica',
 'Crédito fiscal por inversión ángel',
 'Crédito fiscal por gestión financiera',
 'Deducción de GRT por investigación y desarrollo',
 'Crédito fiscal por empleos tecnológicos',
 'Deducción de GRT por software y sitios web en zonas rurales',
 'Crédito fiscal por inversión para fabricantes',
 'Prorrateo por factor único de ventas para fabricantes',
 'Deducción de GRT por insumos para fabricantes',
 'Deducción de GRT por alojamiento web',
]
IND_GROUP_ES = {
 'AEROSPACE/AVIATION': 'AEROESPACIAL Y AVIACIÓN', 'AGRI-BUSINESS': 'AGRONEGOCIOS',
 'CLEAN AND RENEWABLE ENERGY': 'ENERGÍA LIMPIA Y RENOVABLE', 'CREATIVE MEDIA': 'MEDIOS CREATIVOS',
 'FINANCE': 'FINANZAS', 'TECHNOLOGY AND MANUFACTURING': 'TECNOLOGÍA Y MANUFACTURA',
}
DESC_ES = {  # descriptions the print PDF does not carry (widget-only); itsQuest's invented desc is dropped
 'El Paso Electric Company (EPE)': 'Genera y distribuye electricidad en el sur de Nuevo México y el oeste de Texas, incluidos Las Cruces y el condado de Doña Ana.',
 'Las Cruces Utilities': 'Servicios municipales de gas, agua, aguas residuales y residuos sólidos en Las Cruces y sus alrededores; también atiende a los clientes de la Rio Grande Natural Gas Association.',
 'New Mexico Gas Company': 'Servicio de gas natural en gran parte de Nuevo México.',
 'Zia Natural Gas Company': 'Servicio de gas natural para comunidades del sur de Nuevo México, incluidos Hatch y el Valle de Mesilla.',
 'Doña Ana County Utilities': 'Servicios de agua y aguas residuales para las áreas no incorporadas del condado.',
 'Camino Real Regional Utility Authority': 'Servicio de agua y aguas residuales para Sunland Park y Santa Teresa.',
 'Anthony Water & Sanitation District': 'Servicio de agua y saneamiento para el área de Anthony.',
 'Moongate Water Company': 'Empresa privada de agua regulada por la PRC que atiende el área de East Mesa, al este de Las Cruces.',
 'Lake Section Water Company': 'Empresa privada de agua regulada por la PRC que atiende el área de Chaparral.',
 'Elephant Butte Irrigation District (EBID)': 'Suministra agua de riego del Río Grande a tierras agrícolas en todo el Valle de Mesilla.',
 'Comcast Business': 'Servicios de internet, voz y redes para empresas.',
 'CenturyLink': 'Servicios empresariales de internet, voz y fibra.',
 'Segra': 'Red de fibra, datos y servicios de conectividad para empresas y operadores.',
 'Fastwave': 'Proveedor local de internet de alta velocidad para empresas de Las Cruces.',
 'NM Office of Broadband Access & Expansion': 'Mapas de cobertura de banda ancha y programas de subvenciones a nivel estatal, incluidos los fondos federales BEAD.',
 'Las Cruces International Airport': 'Aeropuerto de aviación general en West Mesa con hangares, estacionamiento de aeronaves y terrenos en arrendamiento para empresas de aviación y aeroespaciales.',
}
LABEL_ES = {
 'Alameda Branch': 'Sucursal Alameda', 'Chaparral Center': 'Centro Chaparral', 'City Hall Customer Central': 'Atención al Cliente – Ayuntamiento',
 'East Mesa Campus': 'Campus East Mesa', 'Espina Campus': 'Campus Espina', 'Emergency Center - North Main': 'Centro de Emergencias – North Main',
 'Family Care - Northrise': 'Atención Familiar – Northrise', 'Family Care - Valley': 'Atención Familiar – Valley',
 'Family Medicine Center': 'Centro de Medicina Familiar', 'Gadsden Center': 'Centro Gadsden', 'Hatch Pantry': 'Despensa de Hatch',
 "HealthPlex & Women's Imaging": 'HealthPlex e Imágenes para la Mujer', 'Hospital (Main Campus)': 'Hospital (campus principal)',
 'Imaging Center of Las Cruces': 'Centro de Imágenes de Las Cruces', 'Juntos Project (Family Center)': 'Proyecto Juntos (Centro Familiar)',
 'La Vida Project (Youth Center)': 'Proyecto La Vida (Centro Juvenil)', 'Las Cruces (Central Pantry)': 'Las Cruces (despensa central)',
 'Main': 'Principal', 'Main Bank': 'Sucursal principal', 'Main Office - Las Cruces': 'Oficina principal – Las Cruces',
 'Memorial Cancer Center': 'Centro Oncológico Memorial', 'Orthopedics': 'Ortopedia', 'Pan Am Branch': 'Sucursal Pan Am',
 'Primary Care - Lohman': 'Atención Primaria – Lohman', 'Sonoma Branch': 'Sucursal Sonoma', 'Sun View Imaging Center': 'Centro de Imágenes Sun View',
 'Sunland Park Center': 'Centro Sunland Park', 'Urgent Care - Lohman': 'Atención Urgente – Lohman', 'Urgent Care - Northrise': 'Atención Urgente – Northrise',
 'Urgent Care - Valley': 'Atención Urgente – Valley', 'Utilities Main Office': 'Oficina principal de Servicios Públicos',
 'Workforce Center': 'Centro de Fuerza Laboral', 'Wound Care Center': 'Centro de Cuidado de Heridas',
}
NOTE_MAP = {  # raw research note -> (English, Spanish) ; None drops it
 'Adjacent to Chaparral High School': ('Next to Chaparral High School', 'Junto a Chaparral High School'),
 'Daily 9 a.m.-8 p.m.': ('Daily 9 a.m.–8 p.m.', 'Diario de 9 a.m. a 8 p.m.'),
 'Family Success Center': ('Family Success Center', 'Centro de Éxito Familiar'),
 'Youth Success Center': ('Youth Success Center', 'Centro de Éxito Juvenil'),
 'Freestanding emergency center': ('Freestanding emergency center', 'Centro de emergencias independiente'),
 'Full service; Mon-Thu 9-5, Fri 9-6': ('Full service · Mon–Thu 9–5, Fri 9–6', 'Servicio completo · lun–jue 9–5, vie 9–6'),
 'Full service; across from NMSU Pan American Center; Saturday hours': ('Full service · across from NMSU Pan American Center · Saturday hours', 'Servicio completo · frente al Pan American Center de NMSU · abre los sábados'),
 'Full service; off Hwy 70; Saturday hours': ('Full service · off Hwy 70 · Saturday hours', 'Servicio completo · cerca de la Hwy 70 · abre los sábados'),
 'Houses Customized Training, SBDC, Truck Driving Academy, trades programs': ('Houses Customized Training, SBDC, Truck Driving Academy and trades programs', 'Alberga Capacitación Personalizada, SBDC, Academia de Conducción de Camiones y programas de oficios'),
 'Includes Emergency Room': ('Includes Emergency Room', 'Incluye sala de emergencias'),
 'M-F 8-5; lobby opens 8:30': ('Mon–Fri 8–5 · lobby opens 8:30', 'lun–vie 8–5 · el vestíbulo abre a las 8:30'),
 'Main campus address': None,
 'Main campus emergency department, 24/7': ('Emergency department open 24/7', 'Sala de emergencias abierta 24/7'),
 'Mon-Fri 8am-5pm': ('Mon–Fri 8 a.m.–5 p.m.', 'lun–vie 8 a.m.–5 p.m.'),
 'Mon-Fri 8am-5pm, appointments encouraged': ('Mon–Fri 8 a.m.–5 p.m. · appointments encouraged', 'lun–vie 8 a.m.–5 p.m. · se recomienda cita'),
 'Mon-Fri 9am-6pm': ('Mon–Fri 9 a.m.–6 p.m.', 'lun–vie 9 a.m.–6 p.m.'),
 'MountainView Medical Group': ('MountainView Medical Group', 'MountainView Medical Group'),
 'MountainView Medical Group (from mountainviewdocs.com listing)': ('MountainView Medical Group', 'MountainView Medical Group'),
 'Payment center only, hours vary; call Las Cruces office to confirm': ('Payment center only · hours vary, call the Las Cruces office to confirm', 'Solo centro de pagos · horario variable, llame a la oficina de Las Cruces para confirmar'),
 'Wed and Fri 3-6 p.m.; org site prints ZIP 88047 but Hatch is 87937': ('Wed & Fri 3–6 p.m.', 'mié y vie de 3 a 6 p.m.'),
}

def kick(e):
    return e['group'] or e['category']

# ---- map every PDF English entry to its Spanish twin by (h1, h2, index)
twin = []   # (h1i, h2i, i, en_entry, es_entry)
for h1i, (a, b) in enumerate(zip(PDF_EN, PDF_ES)):
    for h2i, (x, y) in enumerate(zip(a['subsections'], b['subsections'])):
        assert len(x['entries']) == len(y['entries']), x['title']
        for i, (e, f) in enumerate(zip(x['entries'], y['entries'])):
            twin.append((h1i, h2i, i, e, f))
kick_map = {}
for _, _, _, e, f in twin:
    if kick(e) and kick(f):
        kick_map.setdefault(kick(e), kick(f))

def find_twin(h1i, h2i, e):
    cands = [t for t in twin if t[0] == h1i and t[1] == h2i and t[3]['name'] == e['name'] and (kick(t[3]) == kick(e) or not kick(e) or kick(t[3]) == '')]
    if not cands:
        cands = [t for t in twin if t[0] == h1i and t[3]['name'] == e['name']]
    return cands[0] if cands else None

out = copy.deepcopy(BASE)
used = set()
missing = []
for h1i, h1 in enumerate(out):
    h1['title_es'] = PDF_ES[h1i]['title']
    for h2i, h2 in enumerate(h1['subsections']):
        h2['title_es'] = PDF_ES[h1i]['subsections'][h2i]['title']
        ind_i = 0
        for e in h2['entries']:
            # drop research leakage from location notes, translate notes/labels
            for l in e.get('locations', []):
                note = l.get('note', '')
                if note:
                    m = NOTE_MAP.get(note, ('?', '?'))
                    if m is None:
                        l.pop('note')
                    else:
                        assert m[0] != '?', note
                        l['note'], l['note_es'] = m
                if l['label'] in LABEL_ES:
                    l['label_es'] = LABEL_ES[l['label']]
            if e['name'] == "itsQuest, Inc.":
                e['desc'] = ''
            es = {}
            if h2['title'].upper().startswith('INDUSTRY-SPECIFIC'):
                es = {'name': IND_ES[ind_i], 'group': IND_GROUP_ES[e['group']]}
                ind_i += 1
            else:
                t = find_twin(h1i, h2i, e)
                if t is None:
                    missing.append(e['name']); continue
                f = t[4]
                es['name'] = f['name']
                es['desc'] = f['desc'] or DESC_ES.get(e['name'], '')
                k = kick(f) or kick_map.get(kick(e), '')
                if e['group']:
                    es['group'] = k
                elif e['category']:
                    es['category'] = k
                if f['address'] and f['address'] != t[3]['address'] and '@' not in f['address']:
                    es['address'] = f['address']
            e['es'] = {k: v for k, v in es.items() if v}
            if not e['es'].get('desc') and e['desc']:
                pass
        assert ind_i in (0, 25)

# duplicated Licensing city-utility group labels need the Spanish group name too
for h1 in out:
    for h2 in h1['subsections']:
        for e in h2['entries']:
            if h2['title'].upper().startswith('LICENSING') and e['group'] in kick_map:
                e.setdefault('es', {})['group'] = kick_map[e['group']]
            if e['group'] and 'group' not in e.get('es', {}) and e['group'] in kick_map:
                e.setdefault('es', {})['group'] = kick_map[e['group']]
            if e['category'] and 'category' not in e.get('es', {}) and e['category'] in kick_map:
                e.setdefault('es', {})['category'] = kick_map[e['category']]

json.dump(out, open('data/widget_data.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
n = sum(len(h2['entries']) for h1 in out for h2 in h1['subsections'])
noes = [e['name'] for h1 in out for h2 in h1['subsections'] for e in h2['entries'] if not e.get('es')]
nodesc = [e['name'] for h1 in out for h2 in h1['subsections'] for e in h2['entries'] if e['desc'] and not e.get('es', {}).get('desc')]
print('entries', n, '| no twin:', missing, '| no es at all:', noes, '| EN desc but no ES desc:', nodesc)
