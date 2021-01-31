def score_nguyenquan(key):
    s = 0
    key = key[:12]
    for i in {'ng', 'gu', 'uy', 'ye', 'en', 'n ', ' q', 'qu', 'ua','an'}:
        if key.find(i) != -1:
            s = s+1
    for i in {'ngu', 'guy', 'uye', 'yen', 'en ', 'n q',' qu', 'qua', 'uan'}:
        if key.find(i) != -1:
            s = s+3
    for i in {'nguy', 'guye', 'uyen', 'yen ', 'en q', 'n qu', ' qua', 'quan'}:
        if key.find(i) != -1:
            s = s+5        
    return s

def score_dkhk(key):
    s = 0
    key = key[:20]
    for i in {'No', 'oi', 'i ', ' D', 'DK', 'KH', 'HK', 'K ', ' t', 'th', 'hu',
        'uo', 'on', 'ng', 'g ', ' t', 'tr', 'ru', 'u:'}:
        if key.find(i) != -1:
            s = s+1
    for i in {'Noi', 'oi ', 'i D', ' DK', 'DKH', 'KHK', 'HK ', 'K t', ' th',
        'thu', 'huo', 'uon', 'ong', 'ng ', 'g t', ' tr', 'tru','ru:'}:
        if key.find(i) != -1:
            s = s+3
    for i in {'Noi ', 'oi D', 'i DK', ' DKH', 'DKHK', 'KHK ', 'HK t', 'K th',
        ' thu', 'thuo', 'huon','uong','ong ', 'ng t', 'g tr', ' tru', 'tru:'}:
        if key.find(i) != -1:
            s = s+5
    return s

def score_conghoa(key):
    s = 0
    for i in {'CO', 'ON', 'NG', 'G ', ' H', 'HO', 'OA', 'A ','XA', 'A ', ' H',
        'HO', 'OI', 'I ', ' C', 'CH', 'HU', 'U ', ' N', 'NG', 'GH', 'HI', 'IA',
        'A ', ' V', 'VI', 'IE', 'ET', 'T ', ' N', 'NA', 'AM'}:
        if key.find(i) != -1:
            s = s+1
    return s

def score_expired(key):
    key = key[:15]
    s = 0
    for i in {'Co', 'o ', ' g', 'gi', 'ia', 'a ', ' t', 'tr', 'ri',' d', 'de', 'en', 'n:'}:
        if key.find(i) != -1:
            s = s+1
    for i in {'Co ', 'o g', ' gi', 'gia', 'ia ', 'a t', ' tr', 'tri', 'ri ', 'i d', ' de','den','en:'}:
        if key.find(i) != -1:
            s = s+3
    return s

def score_Quoctich_Dantoc(key):
    key = key[:11]
    s = 0
    for i in {'Qu', 'uo', 'oc', 'c ', ' t', 'ti', 'ic', 'ch', 'h:'}:
        if key.find(i) != -1:
            s = s+1
    for i in {'Quo', 'uoc', 'oc ', 'c t',' ti', 'tic', 'ich', 'ch:'}:
        if key.find(i) != -1:
            s = s+3
    for i in {'Quoc', 'uoc ', 'oc t', 'c ti', '  tic', 'tich', 'ich:'}:
        if key.find(i) != -1:
            s = s+5

    for i in {'Da', 'an', 'n ', ' t', 'to', 'oc', 'c:'}:
        if key.find(i) != -1:
            s = s+1
    for i in {'Dan', 'an ', 'n t', ' to', 'toc', 'oc:'}:
        if key.find(i) != -1:
            s = s+3
    for i in {'Dan ', 'an t', 'n to', ' toc', 'toc:'}:
        if key.find(i) != -1:
            s = s+5
    #if len(key) < 20:
    #    s = s+10    
    return s
    
def score_Gioitinh(key):
    key = key[:11]
    s = 0
    for i in {'Gi', 'io','oi', 'i ', ' t', 'ti', 'in', 'nh', 'h:'}:
        if key.find(i) != -1:
            s = s+1
    for i in {'Gio', 'ioi', 'oi ', 'i t', ' ti', 'tin', 'inh', 'nh:'}:
        if key.find(i) != -1:
            s = s+3
    for i in {'Gioi', 'ioi ','oi t', 'i ti', ' tin', 'tinh', 'inh:'}:
        if key.find(i) != -1:
            s = s+5
    return s

def score_Quequan(key):
    key = key[:10]
    s = 0
    for i in {'Qu', 'ue', 'e ', ' q', 'qu', 'ua', 'an', 'n:'}:
        if key.find(i) != -1:
            s = s+1
    for i in {'Que', 'ue ', 'e q', ' qu', 'qua', 'uan', 'an:'}:
        if key.find(i) != -1:
            s = s+3
    for i in {'Que ', 'ue q', 'e qu', ' qua', 'quan', 'uan:'}:
        if key.find(i) != -1:
            s = s+3

    return s 

def score_Noithuongtru(key):
    key = key[:15]
    s = 0
    for i in {'No', 'oi', 'i ', ' t', 'th', 'hu', 'uo', 'on','ng', 'g ', ' t', 'tr', 'ru'}:
        if key.find(i) != -1:
            s = s+1
    for i in {'Noi', 'oi ', 'i t', ' th', 'thu', 'huo', 'uon', 'ong', 'ng ', 'g t', ' tr', 'tru'}:
        if key.find(i) != -1:
            s = s+3
    return s
