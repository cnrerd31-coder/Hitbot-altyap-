// ===== deneme.php =====
<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Hız için buffer'ı kapat
if (ob_get_level()) ob_end_clean();

// --- HEADER ---
header("Content-Type: application/json; charset=UTF-8");

// --- TC PARAMETRESİ ---
$tc = $_GET['tc'] ?? '';
if ($tc === '') {
    echo json_encode(["success" => false, "error" => "TC numarası gerekli"]);
    exit;
}

// --- VERİTABANI BAĞLANTISI ---
try {
    $pdo = new PDO("mysql:host=localhost;dbname=vesika;charset=utf8mb4", "root", "");
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(["success" => false, "error" => "Veritabanı bağlantı hatası: ".$e->getMessage()]);
    exit;
}

// --- TC'YE GÖRE SORGU ---
$stmt = $pdo->prepare("SELECT `VESIKA` FROM `vesika` WHERE `TC` = ? LIMIT 1");
$stmt->execute([$tc]);
$row = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$row) {
    echo json_encode(["success" => false, "error" => "Kayıt bulunamadı"]);
    exit;
}

$base64 = $row['VESIKA'];

// --- HTML MODU ---
if (isset($_GET['format']) && $_GET['format'] === 'html') {
    header("Content-Type: text/html; charset=UTF-8");
    echo "<!DOCTYPE html><html><body style='background:#111;text-align:center;color:#fff;font-family:Arial'>";

    // TC numarası üstte
    echo "<h3>TC: " . htmlspecialchars($tc) . "</h3>";

    // --- Vesika görselinin üstüne: Token ve API Founder ---
    echo "<div style='margin-bottom:10px; padding:5px; background:#222; display:inline-block; border-radius:8px'>";
    echo "<span style='opacity:0.8'>Token: <b>V3QVHHBFwc4OTDN</b> | API Founder: <b>Luna</b></span>";
    echo "</div><br>";

    // Vesika görseli
    echo "<img src='data:image/jpeg;base64," . $base64 . "' style='max-width:90%;border-radius:10px;box-shadow:0 0 15px #000'>";

    echo "</body></html>";
    exit;
}

// --- JSON ÇIKTISI ---
echo json_encode([
    "success" => true,
    "Token" => "V3QVHHBFwc4OTDN",
    "ApiFounder" => "@lunacarma",
    "ApiBilgi" => "bu api @LunaVipSorgu_bot için yazılmıştır.",
    "tc" => $tc,
    "base64" => $base64
], JSON_UNESCAPED_SLASHES);


// ===== dt-api - Kopya.php =====
<!DOCTYPE html>
<html>
<head>
  <title>Plaka Sorgu (SBM'siz)</title>
  <style>
    body { font-family: Arial; background: #f4f4f4; padding: 20px; }
    .box { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; }
    input, button { width: 100%; padding: 12px; margin: 10px 0; }
    button { background: #d32f2f; color: white; border: none; cursor: pointer; }
    pre { background: #eee; padding: 15px; white-space: pre-wrap; }
  </style>
</head>
<body>
<div class="box">
  <h2>Plaka Sorgu (Yasal)</h2>
  <form method="post">
    <input name="p" placeholder="Plaka" required>
    <button>SORGULA</button>
  </form>

  <?php
  if ($_POST['p']) {
    $p = strtoupper($_POST['p']);
    echo "<pre>";
    echo "PLAKA: $p\n";
    echo "────────────────────────────────────\n";

    // MUAYENE
    $ch = curl_init("https://www.tuvturk.com.tr/muayene-sorgulama");
    curl_setopt_array($ch, [CURLOPT_POST=>1, CURLOPT_POSTFIELDS=>http_build_query(['Plaka'=>$p,'AramaTuru'=>'plaka']), CURLOPT_RETURNTRANSFER=>1, CURLOPT_TIMEOUT=>10]);
    $html = curl_exec($ch); curl_close($ch);
    preg_match('/\d{2}\.\d{2}\.\d{4}/', $html, $m);
    echo "MUAYENE: " . ($m[0] ?? "Bulunamadı") . "\n";

    // İHLALLİ GEÇİŞ
    $ch = curl_init("https://ccis.cordisnetwork.com/CWC/bridgeDebt");
    curl_setopt_array($ch, [CURLOPT_POST=>1, CURLOPT_POSTFIELDS=>"query=plakatabtoplamborc&PlateNumber=$p&IsTotalDebtQuery=1&Hash=99331", CURLOPT_RETURNTRANSFER=>1]);
    $html = curl_exec($ch); curl_close($ch);
    preg_match('/(\d+,\d+)/', $html, $m);
    echo "İHLALLİ GEÇİŞ: " . ($m[1] ?? "0,00") . " TL\n";

    // SİGORTA
    echo "SİGORTA: 5664'e '$p' yazıp gönder → cevap gelir\n";

    echo "────────────────────────────────────\n";
    echo "TC / AD / TELEFON: YASAL OLARAK VERİLEMEZ\n";
    echo "</pre>";
  }
  ?>
</div>
</body>
</html>


// ===== dt-api.php =====
<?php
// ====================================================
// DRAGON V80 – %100 TEMİZ JSON
// HİÇBİR SCRIPT, HİÇBİR HTML, HİÇBİR EKSTRA YOK!
// SEKME AÇMA YOK – SADECE SONUÇ!
// ====================================================

ob_start(); // Çıktıyı yakala

$tc = $_GET['tc'] ?? '';
if (!preg_match('/^\d{11}$/', $tc)) {
    $result = ["success"=>false,"error"=>"11 haneli TC gir","footer"=>"API-BY-LUNA"];
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// 101m'den doğum tarihi
$conn = new mysqli("localhost", "root", "", "101m");
if ($conn->connect_error) {
    $result = ["success"=>false,"error"=>"DB hatası","footer"=>"API-BY-LUNA"];
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

$stmt = $conn->prepare("SELECT DOGUMTARIHI FROM `101m` WHERE TC = ?");
$stmt->bind_param("s", $tc);
$stmt->execute();
$res = $stmt->get_result();

if ($res->num_rows === 0) {
    $result = ["success"=>false,"error"=>"TC bulunamadı","tc"=>$tc,"footer"=>"API-BY-LUNA"];
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

$dogum_tarihi = trim($res->fetch_assoc()['DOGUMTARIHI']);
$stmt->close();
$conn->close();

// Format → 10.03.1949
$dt = DateTime::createFromFormat('Y-m-d', $dogum_tarihi)
    ?: DateTime::createFromFormat('d.m.Y', $dogum_tarihi)
    ?: DateTime::createFromFormat('d/m/Y', $dogum_tarihi);

if (!$dt) {
    $result = ["success"=>false,"error"=>"Tarih okunamadı","footer"=>"API-BY-LUNA"];
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

$formatted_dt = $dt->format('d.m.Y');
$target_url = "http://localhost:8031/api/adres?tc=$tc&dt=$formatted_dt";

// SONUCU ÇEK
$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL => $target_url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_SSL_VERIFYPEER => false,
    CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    CURLOPT_HTTPHEADER => [
        'Accept: application/json',
        'Referer: http://localhost:8031/',
        'Origin: http://localhost:8031'
    ]
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// HATA KONTROL
if (!$response || $http_code !== 200) {
    $error = json_decode($response, true) ?: ["raw" => substr($response, 0, 500)];
    $error['success'] = false;
    $error['error'] = $error['error'] ?? "Bağlantı hatası (HTTP: $http_code)";
    $error['footer'] = "API-BY-LUNA";
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($error, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    ob_end_flush();
    exit;
}

// BAŞARILI → TEMİZ JSON + FOOTER
$result = json_decode($response, true);
$result['footer'] = "API-BY-LUNA";

header('Content-Type: application/json; charset=utf-8');
echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);

ob_end_flush();
exit;


// ===== 101m/101m-ad-ad2-soyad-nufusil.php =====
<?php
header('Content-Type: application/json; charset=utf-8');

// GET parametrelerini al ve decode et
$ad = isset($_GET['ad']) ? trim(urldecode($_GET['ad'])) : '';
$soyad = isset($_GET['soyad']) ? trim(urldecode($_GET['soyad'])) : '';
$il = isset($_GET['il']) ? trim(urldecode($_GET['il'])) : '';
$ilce = isset($_GET['ilce']) ? trim(urldecode($_GET['ilce'])) : '';

// ad parametresini = ile ayırarak birleştir
$ad_parts = explode('=', $ad); // MEHMET=EMİN -> ['MEHMET', 'EMİN']
$ad = implode(' ', array_map('trim', $ad_parts)); // MEHMET EMİN

// Giriş parametrelerini logla
error_log("Giriş: ad=$ad, soyad=$soyad, il=$il, ilce=$ilce");

// Veritabanı bağlantı bilgileri
$host = "localhost";
$user = "root";
$password = ""; // Şifrenizi buraya girin
$dbname = "101m";

try {
    // PDO ile veritabanı bağlantısı
    $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $user, $password, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4"
    ]);
} catch (PDOException $e) {
    error_log("Bağlantı Hatası: " . $e->getMessage());
    http_response_code(500);
    die(json_encode(['error' => 'Veritabanı bağlantısı başarısız: ' . $e->getMessage()], JSON_UNESCAPED_UNICODE));
}

// Parametre doğrulama
if (empty($ad) || empty($soyad)) {
    error_log("Hata: ad ve soyad eksik.");
    http_response_code(400);
    die(json_encode(['error' => 'ad ve soyad parametreleri zorunludur.'], JSON_UNESCAPED_UNICODE));
}

// SQL sorgusu
$sql = "SELECT 
            id,
            TC AS tc,
            ADI AS ad,
            SOYADI AS soyad,
            DOGUMTARIHI AS dogum_tarihi,
            NUFUSIL AS nufus_il,
            NUFUSILCE AS nufus_ilce,
            ANNEADI AS anne_adi,
            ANNETC AS anne_tc,
            BABAADI AS baba_adi,
            BABATC AS baba_tc,
            UYRUK AS uyruk
        FROM 101m 
        WHERE ADI = :ad AND SOYADI = :soyad";
$params = [
    ':ad' => $ad,
    ':soyad' => $soyad
];

// Opsiyonel il filtresi
if (!empty($il)) {
    $sql .= " AND NUFUSIL = :il";
    $params[':il'] = $il;
}

// Opsiyonel ilce filtresi
if (!empty($ilce)) {
    $sql .= " AND NUFUSILCE = :ilce";
    $params[':ilce'] = $ilce;
}

// Sorguyu logla
error_log("SQL: $sql, Parametreler: " . json_encode($params, JSON_UNESCAPED_UNICODE));

try {
    // Sorguyu hazırla ve çalıştır
    $start = microtime(true);
    $stmt = $conn->prepare($sql);
    $stmt->execute($params);

    $data = [];

    if ($stmt->rowCount() > 0) {
        while ($row = $stmt->fetch()) {
            // Tam eşleşme kontrolü
            if ($row['ad'] === $ad && $row['soyad'] === $soyad && (empty($il) || $row['nufus_il'] === $il) && (empty($ilce) || $row['nufus_ilce'] === $ilce)) {
                $data[] = array_map(function($value) {
                    return htmlspecialchars($value ?? 'Bulunamadı', ENT_QUOTES, 'UTF-8');
                }, $row);
                error_log("Eşleşen Kayıt: " . json_encode($row, JSON_UNESCAPED_UNICODE));
            }
        }
    }

    // Eğer veri yoksa, "Bulunamadı" yanıtı
    if (empty($data)) {
        error_log("Kayıt bulunamadı.");
        $data[] = [
            'id' => 'Bulunamadı',
            'tc' => 'Bulunamadı',
            'ad' => 'Bulunamadı',
            'soyad' => 'Bulunamadı',
            'dogum_tarihi' => 'Bulunamadı',
            'nufus_il' => 'Bulunamadı',
            'nufus_ilce' => 'Bulunamadı',
            'anne_adi' => 'Bulunamadı',
            'anne_tc' => 'Bulunamadı',
            'baba_adi' => 'Bulunamadı',
            'baba_tc' => 'Bulunamadı',
            'uyruk' => 'Bulunamadı'
        ];
    }

    // Performans loglama
    $duration = microtime(true) - $start;
    error_log("Sorgu süresi: $duration saniye");

} catch (PDOException $e) {
    error_log("Sorgu Hatası: " . $e->getMessage());
    http_response_code(500);
    die(json_encode(['error' => 'Sorgu hatası: ' . $e->getMessage()], JSON_UNESCAPED_UNICODE));
}

// JSON çıktısı
$output = [
    'success' => true,
    'telegram' => 'Luna Vip Panel',
    'author' => 'by Luna',
    'api ismi' => 'Ad Soyad İl İlçe Sorgu',
    'data' => $data
];

echo json_encode($output, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

// Bağlantıyı kapat
$conn = null;
?>


// ===== 101m/101m-ad-ad2-soyad-simple.php =====
<?php
header('Content-Type: application/json; charset=utf-8');

$adi = isset($_GET['adi']) ? trim($_GET['adi']) : '';
$soyadi = isset($_GET['soyadi']) ? trim($_GET['soyadi']) : '';
$nufusil = isset($_GET['nufusil']) ? trim($_GET['nufusil']) : '';

if (!$adi || !$soyadi) {
    die(json_encode(["error" => "Ad ve soyad zorunludur."], JSON_UNESCAPED_UNICODE));
}

try {
    $conn = new mysqli("localhost", "root", "", "101m");
    $conn->set_charset("utf8mb4");
    
    // Türkçe uppercase
    $adi = mb_strtoupper($adi, 'UTF-8');
    $soyadi = mb_strtoupper($soyadi, 'UTF-8');
    $nufusil = $nufusil ? mb_strtoupper($nufusil, 'UTF-8') : '';
    
    // Ad sözcükleri ayrı ayrı
    $ad_parcalar = array_filter(explode(' ', trim($adi)));
    
    // WHERE koşulları
    $where = [];
    $params = [];
    $types = '';
    
    foreach ($ad_parcalar as $kelime) {
        $where[] = "UPPER(ADI) LIKE ?";
        $params[] = "%$kelime%";
        $types .= 's';
    }
    
    $where[] = "UPPER(SOYADI) LIKE ?";
    $params[] = "%$soyadi%";
    $types .= 's';
    
    if ($nufusil) {
        $where[] = "UPPER(NUFUSIL) = ?";
        $params[] = $nufusil;
        $types .= 's';
    }
    
    $where_clause = implode(" AND ", $where);
    
    $sql = "
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m`
        WHERE $where_clause
        ORDER BY ADI ASC, SOYADI ASC
        LIMIT 50000
    ";
    
    $stmt = $conn->prepare($sql);
    $stmt->bind_param($types, ...$params);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $data = [];
    while ($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
    
    if (empty($data)) {
        echo json_encode(["success" => false, "message" => "Bulunamadı"], JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(["success" => true, "data" => $data, "footer" => "API-BY-LUNA"], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
    
} catch (Exception $e) {
    die(json_encode(["error" => "DB Error: " . $e->getMessage()], JSON_UNESCAPED_UNICODE));
}
?>


// ===== 101m/101m-ad-ad2-soyad-v2.php =====
<?php
// GÜVENLİ 2 İSİMLİ SORGU (v2)
require_once __DIR__ . '/../config/DatabaseConnection.php';
require_once __DIR__ . '/../config/APIHelper.php';

header('Content-Type: application/json; charset=utf-8');

// Parametreleri al
$adi = APIHelper::getParam('adi', '');
$soyadi = APIHelper::getParam('soyadi', '');
$nufusil = APIHelper::getParam('nufusil', '');

if (!$adi || !$soyadi) {
    APIHelper::error('Ad ve soyad parametreleri zorunludur.');
}

try {
    $conn = DatabaseConnection::getMysqli('101m');
    
    // Türkçe karakterleri uppercase yap
    $adi = mb_strtoupper($adi, 'UTF-8');
    $soyadi = mb_strtoupper($soyadi, 'UTF-8');
    $nufusil = $nufusil ? mb_strtoupper($nufusil, 'UTF-8') : '';
    
    // Ad sözcükleri ayrı ayrı ara
    $ad_parcalar = array_filter(explode(' ', trim($adi)));
    
    // WHERE koşulları
    $conditions = [];
    $params = [];
    $types = '';
    
    // Her ad sözcüğü için LIKE koşulu
    foreach ($ad_parcalar as $kelime) {
        $conditions[] = "UPPER(ADI) LIKE ?";
        $params[] = "%$kelime%";
        $types .= 's';
    }
    
    // Soyad
    $conditions[] = "UPPER(SOYADI) LIKE ?";
    $params[] = "%$soyadi%";
    $types .= 's';
    
    // İl (opsiyonel)
    if ($nufusil) {
        $conditions[] = "UPPER(NUFUSIL) = ?";
        $params[] = $nufusil;
        $types .= 's';
    }
    
    $where_clause = implode(" AND ", $conditions);
    
    $sql = "
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m`
        WHERE $where_clause
        ORDER BY ADI ASC, SOYADI ASC
        LIMIT 50000
    ";
    
    $stmt = $conn->prepare($sql);
    
    if (!$stmt) {
        throw new Exception("Sorgu hazırlanırken hata: " . $conn->error);
    }
    
    // Parametreleri bind et
    $stmt->bind_param($types, ...$params);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $data = [];
    while ($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
    
    if (empty($data)) {
        APIHelper::response(false, null, 'Sonuç bulunamadı.');
    }
    
    APIHelper::response(true, $data, null, 'API-BY-LUNA');
    
} catch (Exception $e) {
    APIHelper::error('Sorgu hatası', $e->getMessage());
}
?>


// ===== 101m/101m-ad-ad2-soyad.php =====
<?php
// 101m-ad-ad2-soyad.php → IŞIN HIZINDA + LIMITSIZ + %100 DOĞRU SONUÇ
header('Content-Type: application/json; charset=utf-8');

// Hızlı bağlantı + hata gizleme (gerekirse açarsın)
// error_reporting(0);

$conn = new mysqli("localhost", "root", "", "101m");
if ($conn->connect_error) {
    die(json_encode(["hata" => "Bağlantı hatası"]));
}
$conn->set_charset("utf8mb4");

// === BU KISIM KRİTİK: NORMALİZE ALANLAR OLUŞTUR (BİR KERE ÇALIŞTIR) ===
// Bu komutları phpMyAdmin veya terminalde 1 kez çalıştır:
// ALTER TABLE 101m ADD COLUMN IF NOT EXISTS ADI_NORM VARCHAR(255) GENERATED ALWAYS AS (UPPER(ADI)) STORED;
// ALTER TABLE 101m ADD COLUMN IF NOT EXISTS SOYADI_NORM VARCHAR(255) GENERATED ALWAYS AS (UPPER(SOYADI)) STORED;
// ALTER TABLE 101m ADD COLUMN IF NOT EXISTS NUFUSIL_NORM VARCHAR(100) GENERATED ALWAYS AS (UPPER(NUFUSIL)) STORED;
// CREATE INDEX IF NOT EXISTS idx_ara ON 101m(ADI_NORM, SOYADI_NORM, NUFUSIL_NORM);

// Eğer yukarıdaki alanlar yoksa, geçici olarak eski yöntemle çalışsın:
$use_generated = true;
$result = $conn->query("SHOW COLUMNS FROM 101m LIKE 'ADI_NORM'");
if ($result->num_rows == 0) $use_generated = false;

$adi_raw    = trim($_GET['adi'] ?? '');
$soyadi_raw = trim($_GET['soyadi'] ?? '');
$nufusil    = trim($_GET['nufusil'] ?? '');

if ($adi_raw === '' || $soyadi_raw === '') {
    die(json_encode(["hata" => "Ad ve soyad zorunlu"]));
}

// Türkçe karakterleri düzeltmeden direkt UPPER yapıyoruz (MySQL zaten hallediyor)
$ad_parcalar   = array_filter(explode(' ', mb_strtoupper($adi_raw, 'UTF-8')));
$soyadi_upper  = mb_strtoupper($soyadi_raw, 'UTF-8');
$nufusil_upper = $nufusil !== '' ? mb_strtoupper($nufusil, 'UTF-8') : null;

// Sorgu hazırlığı
$conditions = [];
$params = [];
$types = '';

foreach ($ad_parcalar as $kelime) {
    if ($use_generated) {
        $conditions[] = "ADI_NORM LIKE ?";
    } else {
        $conditions[] = "UPPER(ADI) LIKE ?";
    }
    $params[] = "%$kelime%";
    $types .= 's';
}

if ($use_generated) {
    $conditions[] = "SOYADI_NORM LIKE ?";
} else {
    $conditions[] = "UPPER(SOYADI) LIKE ?";
}
$params[] = $soyadi_upper;
$types .= 's';

if ($nufusil_upper !== null) {
    if ($use_generated) {
        $conditions[] = "NUFUSIL_NORM = ?";
    } else {
        $conditions[] = "UPPER(NUFUSIL) = ?";
    }
    $params[] = $nufusil_upper;
    $types .= 's';
}

$sql = "SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE, ANNEADI, ANNETC, BABAADI, BABATC, UYRUK 
        FROM 101m 
        WHERE " . implode(" AND ", $conditions) . " 
        ORDER BY ADI ASC";

$stmt = $conn->prepare($sql);
if (!$stmt) {
    die(json_encode(["hata" => "Sorgu hatası"]));
}

if (!empty($params)) {
    $stmt->bind_param($types, ...$params);
}

$stmt->execute();
$result = $stmt->get_result();
$data = $result->fetch_all(MYSQLI_ASSOC);

if (empty($data)) {
    echo json_encode(["hata" => "Sonuç bulunamadı."]);
} else {
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
}

$stmt->close();
$conn->close();
?>


// ===== 101m/101m-ad-soyad-nufusil.php =====
<?php
header('Content-Type: application/json; charset=utf-8');

// GET parametrelerini al
$ad = isset($_GET['ad']) ? trim($_GET['ad']) : '';
$soyad = isset($_GET['soyad']) ? trim($_GET['soyad']) : '';
$il = isset($_GET['il']) ? trim($_GET['il']) : '';
$ilce = isset($_GET['ilce']) ? trim($_GET['ilce']) : '';

// Veritabanı bağlantı bilgileri
$host = "localhost";
$user = "root";
$password = ""; // Şifrenizi buraya girin
$dbname = "101m";

try {
    // PDO ile veritabanı bağlantısı
    $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $user, $password, [
        PDO::ATTR_PERSISTENT => true,
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);
} catch (PDOException $e) {
    http_response_code(500);
    die(json_encode(['error' => 'Veritabanı bağlantısı başarısız.'], JSON_UNESCAPED_UNICODE));
}

// Parametre doğrulama
if ((!empty($ilce) && empty($il)) || ((!empty($il) && (empty($ad) || empty($soyad))))) {
    http_response_code(400);
    die(json_encode(['error' => 'Lütfen parametreleri doğru şekilde kullanın'], JSON_UNESCAPED_UNICODE));
}

if (empty($ad) || empty($soyad)) {
    http_response_code(400);
    die(json_encode(['error' => 'Lütfen adi ve soyadi parametrelerini girin.'], JSON_UNESCAPED_UNICODE));
}

// SQL sorgusu - Tüm alanları seç
$sql = "SELECT 
            id,
            TC AS tc,
            ADI AS ad,
            SOYADI AS soyad,
            DOGUMTARIHI AS dogum_tarihi,
            NUFUSIL AS nufus_il,
            NUFUSILCE AS nufus_ilce,
            ANNEADI AS anne_adi,
            ANNETC AS anne_tc,
            BABAADI AS baba_adi,
            BABATC AS baba_tc,
            UYRUK AS uyruk
        FROM 101m 
        WHERE 1=1";
$params = [];

// Filtreleme: ad ve soyad (tam eşleşme)
if (!empty($ad) && !empty($soyad)) {
    $sql .= " AND ADI = :ad AND SOYADI = :soyad";
    $params[':ad'] = $ad;
    $params[':soyad'] = $soyad;
}

// Opsiyonel filtreler: il ve ilce
if (!empty($il)) {
    $sql .= " AND NUFUSIL = :il";
    $params[':il'] = $il;
}
if (!empty($ilce)) {
    $sql .= " AND NUFUSILCE = :ilce";
    $params[':ilce'] = $ilce;
}

try {
    // Sorguyu hazırla ve çalıştır
    $start = microtime(true); // Performans ölçümü
    $stmt = $conn->prepare($sql);
    $stmt->execute($params);

    $data = [];

    if ($stmt->rowCount() > 0) {
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            foreach ($row as $key => $value) {
                $row[$key] = htmlspecialchars($value ?? 'Bulunamadı', ENT_QUOTES, 'UTF-8');
            }
            $data[] = $row;
        }
    } else {
        // Varsayılan "Bulunamadı" yanıtı
        $data[] = [
            'id' => 'Bulunamadı',
            'tc' => 'Bulunamadı',
            'ad' => 'Bulunamadı',
            'soyad' => 'Bulunamadı',
            'dogum_tarihi' => 'Bulunamadı',
            'nufus_il' => 'Bulunamadı',
            'nufus_ilce' => 'Bulunamadı',
            'anne_adi' => 'Bulunamadı',
            'anne_tc' => 'Bulunamadı',
            'baba_adi' => 'Bulunamadı',
            'baba_tc' => 'Bulunamadı',
            'uyruk' => 'Bulunamadı'
        ];
    }

    // Performans loglama
    $duration = microtime(true) - $start;
    error_log("Sorgu süresi: $duration saniye");

} catch (PDOException $e) {
    http_response_code(500);
    die(json_encode(['error' => 'Sorgu hatası.'], JSON_UNESCAPED_UNICODE));
}

// JSON çıktısı
$output = [
    'success' => true,
    'telegram' => 'Luna Vip Panel',
    'author' => 'by Luna',
    'api ismi' => 'Ad Soyad İl İlçe Sorgu',
    'data' => $data
];

echo json_encode($output, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

// Bağlantıyı kapat
$conn = null;
?>


// ===== 101m/101m-ad-soyad-v2.php =====
<?php
// GÜVENLİ AD-SOYAD SORGUSU (v2)
require_once __DIR__ . '/../config/DatabaseConnection.php';
require_once __DIR__ . '/../config/APIHelper.php';

header('Content-Type: application/json; charset=utf-8');

// Parametreleri al
$adi = APIHelper::getParam('adi', '');
$soyadi = APIHelper::getParam('soyadi', '');
$nufusil = APIHelper::getParam('nufusil', '');

if (!$adi || !$soyadi) {
    APIHelper::error('Ad ve soyad parametreleri zorunludur.');
}

try {
    $conn = DatabaseConnection::getMysqli('101m');
    
    // Türkçe karakterleri uppercase yap
    $adi = mb_strtoupper($adi, 'UTF-8');
    $soyadi = mb_strtoupper($soyadi, 'UTF-8');
    $nufusil = $nufusil ? mb_strtoupper($nufusil, 'UTF-8') : '';
    
    // Sorgu hazırla
    $where = "UPPER(ADI) LIKE ? AND UPPER(SOYADI) LIKE ?";
    $params = ["%$adi%", "%$soyadi%"];
    $types = "ss";
    
    if ($nufusil) {
        $where .= " AND UPPER(NUFUSIL) = ?";
        $params[] = $nufusil;
        $types .= "s";
    }
    
    $sql = "
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m`
        WHERE $where
        ORDER BY ADI ASC, SOYADI ASC
        LIMIT 10000
    ";
    
    $stmt = $conn->prepare($sql);
    
    if (!$stmt) {
        throw new Exception("Sorgu hazırlanırken hata: " . $conn->error);
    }
    
    // Parametreleri bind et (dinamik)
    $stmt->bind_param($types, ...$params);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $data = [];
    while ($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
    
    if (empty($data)) {
        APIHelper::response(false, null, 'Sonuç bulunamadı.');
    }
    
    APIHelper::response(true, $data, null, 'API-BY-LUNA');
    
} catch (Exception $e) {
    APIHelper::error('Sorgu hatası', $e->getMessage());
}
?>


// ===== 101m/101m-ad-soyad.php =====
<?php
// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbname = "101m"; // Veritabanı adı

// Veritabanına bağlan
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantısı başarısız: " . $conn->connect_error], JSON_PRETTY_PRINT));
}

// API'yi kullanarak sorgulama parametrelerini al
$adi = $_GET['adi'] ?? '';
$soyadi = $_GET['soyadi'] ?? '';
$nufusil = $_GET['nufusil'] ?? '';

if ($adi && $soyadi) {
    // ADI ve SOYADI parametrelerine göre veritabanında arama yap
    if ($nufusil) {
        $stmt = $conn->prepare("SELECT * FROM `101m` WHERE ADI = ? AND SOYADI = ? AND NUFUSIL = ?");
        $stmt->bind_param("sss", $adi, $soyadi, $nufusil);
    } else {
        $stmt = $conn->prepare("SELECT * FROM `101m` WHERE ADI = ? AND SOYADI = ?");
        $stmt->bind_param("ss", $adi, $soyadi);
    }
    
    if ($stmt === false) {
        die(json_encode(["error" => "SQL sorgusu hazırlanırken hata oluştu: " . $conn->error], JSON_PRETTY_PRINT));
    }

    $stmt->execute();
    $result = $stmt->get_result();

    if ($result === false) {
        die(json_encode(["error" => "SQL sorgusu çalıştırılırken hata oluştu: " . $stmt->error], JSON_PRETTY_PRINT));
    }

    $users = [];
    while ($row = $result->fetch_assoc()) {
        $users[] = $row;
    }

    header('Content-Type: application/json');
    if (empty($users)) {
        echo json_encode(["error" => "Belirtilen kriterlere ait kayıt bulunamadı."], JSON_PRETTY_PRINT);
    } else {
        echo json_encode($users, JSON_PRETTY_PRINT);
    }

    // Prepared statement'i kapat
    $stmt->close();
} else {
    echo json_encode(["error" => "Lütfen adi ve soyadi parametrelerini girin."], JSON_PRETTY_PRINT);
}

// Veritabanı bağlantısını kapat
$conn->close();
?>


// ===== 101m/101m-tc-sorgulama-simple.php =====
<?php
header('Content-Type: application/json; charset=utf-8');

$tc = isset($_GET['tc']) ? trim($_GET['tc']) : '';

if (!$tc || !preg_match('/^\d{11}$/', $tc)) {
    die(json_encode(["error" => "Geçersiz TC numarası."], JSON_UNESCAPED_UNICODE));
}

try {
    $conn = new mysqli("localhost", "root", "", "101m");
    $conn->set_charset("utf8mb4");
    
    $stmt = $conn->prepare("
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m`
        WHERE TC = ?
        LIMIT 1
    ");
    
    $stmt->bind_param("s", $tc);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        echo json_encode(["success" => false, "message" => "Bulunamadı"], JSON_UNESCAPED_UNICODE);
    } else {
        $data = $result->fetch_assoc();
        echo json_encode(["success" => true, "data" => $data, "footer" => "API-BY-LUNA  "], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
    
} catch (Exception $e) {
    die(json_encode(["error" => "DB Error: " . $e->getMessage()], JSON_UNESCAPED_UNICODE));
}
?>


// ===== 101m/101m-tc-sorgulama-sulale.php =====
<?php
// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbname = "101m"; // Veritabanı adı

// Veritabanına bağlan
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantısı başarısız: " . $conn->connect_error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// API'yi kullanarak sorgulama parametrelerini al
$tc = $_GET['tc'] ?? '';

if ($tc) {
    $all_users = [];
    $visited_tcs = [];
    $tc_queue = [$tc];

    while (!empty($tc_queue)) {
        $current_tc = array_shift($tc_queue);

        // Ziyaret edilen TC numaralarını kontrol et
        if (in_array($current_tc, $visited_tcs)) {
            continue;
        }
        
        // TC numarasına göre veritabanında arama yap
        $stmt = $conn->prepare("SELECT * FROM `101m` WHERE TC = ?");
        if ($stmt === false) {
            die(json_encode(["error" => "SQL sorgusu hazırlanırken hata oluştu: " . $conn->error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        }

        $stmt->bind_param("s", $current_tc);
        $stmt->execute();
        $result = $stmt->get_result();

        if ($result === false) {
            die(json_encode(["error" => "SQL sorgusu çalıştırılırken hata oluştu: " . $stmt->error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        }

        while ($row = $result->fetch_assoc()) {
            $all_users[] = $row;

            // Anne ve baba TC numaralarını sorgu kuyruğuna ekle
            if (!empty($row['ANNETC']) && !in_array($row['ANNETC'], $visited_tcs)) {
                $tc_queue[] = $row['ANNETC'];
            }
            if (!empty($row['BABATC']) && !in_array($row['BABATC'], $visited_tcs)) {
                $tc_queue[] = $row['BABATC'];
            }
        }

        // Ziyaret edilen TC numarasını işaretle
        $visited_tcs[] = $current_tc;
    }

    header('Content-Type: application/json; charset=UTF-8');
    echo json_encode($all_users, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

    // Prepared statement'i kapat
    $stmt->close();
} else {
    echo json_encode(["error" => "Lütfen bir TC numarası girin."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}

// Veritabanı bağlantısını kapat
$conn->close();
?>


// ===== 101m/101m-tc-sorgulama-v2.php =====
<?php
// GÜVENLİ TC SORGUSU (v2)
require_once __DIR__ . '/../config/DatabaseConnection.php';
require_once __DIR__ . '/../config/APIHelper.php';

header('Content-Type: application/json; charset=utf-8');

// TC'yi al ve doğrula
$tc = APIHelper::getParam('tc', '', '/^\d{11}$/');

if (!$tc) {
    APIHelper::error('Geçersiz TC numarası. 11 haneli sayı girin.');
}

try {
    $conn = DatabaseConnection::getMysqli('101m');
    
    // Prepared statement kullan
    $stmt = $conn->prepare("
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE, 
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m` 
        WHERE TC = ?
        LIMIT 1
    ");
    
    if (!$stmt) {
        throw new Exception("Sorgu hazırlanırken hata: " . $conn->error);
    }
    
    $stmt->bind_param("s", $tc);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        APIHelper::response(false, null, 'Bu TC numarasına ait kayıt bulunamadı.');
    }
    
    $data = $result->fetch_assoc();
    APIHelper::response(true, $data, null, 'API-BY-LUNA');
    
} catch (Exception $e) {
    APIHelper::error('Sorgu hatası', $e->getMessage());
}
?>


// ===== 101m/101m-tc-sorgulama.php =====
<?php
// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbname = "101m"; // Veritabanı adı

// Veritabanına bağlan
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantısı başarısız: " . $conn->connect_error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// API'yi kullanarak sorgulama parametrelerini al
$tc = $_GET['tc'] ?? '';

if ($tc) {
    // TC parametresine göre veritabanında arama yap
    $stmt = $conn->prepare("SELECT * FROM `101m` WHERE TC = ?");
    if ($stmt === false) {
        die(json_encode(["error" => "SQL sorgusu hazırlanırken hata oluştu: " . $conn->error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    $stmt->bind_param("s", $tc);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result === false) {
        die(json_encode(["error" => "SQL sorgusu çalıştırılırken hata oluştu: " . $stmt->error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    $users = [];
    while ($row = $result->fetch_assoc()) {
        // Verileri okunabilir hale getir
        $users[] = [
            "ID" => $row["id"],
            "TC Kimlik Numarası" => $row["TC"],
            "Adı" => $row["ADI"],
            "Soyadı" => $row["SOYADI"],
            "Doğum Tarihi" => $row["DOGUMTARIHI"],
            "Nüfus İl" => $row["NUFUSIL"],
            "Nüfus İlçe" => $row["NUFUSILCE"],
            "Anne Adı" => $row["ANNEADI"],
            "Anne TC" => $row["ANNETC"],
            "Baba Adı" => $row["BABAADI"],
            "Baba TC" => $row["BABATC"],
            "Uyruk" => $row["UYRUK"] ?? "Bilinmiyor"
        ];
    }

    header('Content-Type: application/json');
    if (empty($users)) {
        echo json_encode(["error" => "Belirtilen TC numarasına ait kayıt bulunamadı.", "footer" => "API-BY-LUNA"], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(["data" => $users, "footer" => "API-BY-LUNA"], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }

    // Prepared statement'i kapat
    $stmt->close();
} else {
    echo json_encode(["error" => "Lütfen bir TC numarası girin.", "footer" => "API-BY-LUNA"], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}

// Veritabanı bağlantısını kapat
$conn->close();
?>


// ===== 101m/ail.php =====
<?php
error_reporting(0);
header('Content-Type: application/json; charset=UTF-8');

function kisiBilgileriGetir($tc) {
    $servername = "localhost";
    $username = "root";
    $password = "";
    $dbname = "101m";
    $conn = new mysqli($servername, $username, $password, $dbname);

    $KimlikNo = strtoupper(mysqli_real_escape_string($conn, $tc));

    $sql = "SELECT * FROM 101m WHERE TC = '" . $KimlikNo . "'";

    $result = $conn->query($sql);
    $row = $result->fetch_assoc();

    if ($result->num_rows > 0)
    {
        return array(
            "Status" => true,
            "KendiKimlikNo" => $row['TC'],
            "EşininKimlikNo" => $row['TC'],
            "AnneKimlikNo" => $row['ANNETC'],
            "BabaKimlikNo" => $row['BABATC']
        );
    } else
    {
        echo json_encode(array(
            'Status' => false,
            'Message' => 'Aradığınız kişiye ait aile bilgisi bulunamadı!'
        ), JSON_UNESCAPED_UNICODE);
        exit;
    }
}

function kisiAnneBabaGetir($tc)
{
    $kisibilgi = kisiBilgileriGetir($tc);
    $servername = "localhost";
    $username = "root";
    $password = "";
    $dbname = "101m";
    $conn = new mysqli($servername, $username, $password, $dbname);

    $AnneKimlikNo = strtoupper(mysqli_real_escape_string($conn, $kisibilgi["AnneKimlikNo"]));
    $BabaKimlikNo = strtoupper(mysqli_real_escape_string($conn, $kisibilgi["BabaKimlikNo"]));

    $sql = "SELECT * FROM 101m WHERE TC = '" . $AnneKimlikNo . "'";

    $aileArray = array();
    $result = $conn->query($sql);
    $row = $result->fetch_assoc();

    $sql2 = "SELECT * FROM 101m WHERE TC = '" . $BabaKimlikNo . "'";

    $result2 = $conn->query($sql2);
    $row2 = $result2->fetch_assoc();

    if ($result->num_rows > 0)
    {
        array_push($aileArray, array(
            "Yakınlık" => "Annesi",
            "KimlikNo" => $row['TC'],
            "Isim" => $row['ADI'],
            "Soyisim" => $row['SOYADI'],
            "DogumTarihi" => $row['DOGUMTARIHI'],
            "NufusIl" => $row['NUFUSIL'],
            "NufusIlce" => $row['NUFUSILCE'],
            "AnneIsim" => $row['ANNEADI'],
            "AnneKimlikNo" => $row['ANNETC'],
            "BabaIsim" => $row['BABAADI'],
            "BabaKimlikNo" => $row['BABATC'],
            "Uyruk" => $row['UYRUK'],

        ));
    } else {
        return array(
            "Status" => false,
            "Message" => "Aradığınız kişiye ait aile bilgisi bulunamadı!"
        );
    }

    if($result2->num_rows > 0)
    {
        array_push($aileArray, array(
            "Yakınlık" => "Babası",
            "KimlikNo" => $row2['TC'],
            "Isim" => $row2['ADI'],
            "Soyisim" => $row2['SOYADI'],
            "DogumTarihi" => $row2['DOGUMTARIHI'],
            "NufusIl" => $row2['NUFUSIL'],
            "NufusIlce" => $row2['NUFUSILCE'],
            "AnneIsim" => $row2['ANNEADI'],
            "AnneKimlikNo" => $row2['ANNETC'],
            "BabaIsim" => $row2['BABAADI'],
            "BabaKimlikNo" => $row2['BABATC'],
            "Uyruk" => $row2['UYRUK'],
       
        ));
    } else {
        return array(
            "Status" => false,
            "Message" => "Aradığınız kişiye ait aile bilgisi bulunamadı!"
        );
    }
    return $aileArray;
}

function cocukBilgisiGetirYetiskin($tc)
{
    $kisibilgi = kisiBilgileriGetir($tc);

    $servername = "localhost";
    $username = "root";
    $password = "";
    $dbname = "101m";
    $conn = new mysqli($servername, $username, $password, $dbname);
    
    $AnneKimlikNo = strtoupper(mysqli_real_escape_string($conn, $kisibilgi["KendiKimlikNo"]));

    $sql = "SELECT * FROM 101m WHERE ANNETC = '" . $AnneKimlikNo . "'";
    $result = $conn->query($sql);

    $cocukArray = array();
    if ($result->num_rows > 0)
    {
        while ($row = $result->fetch_assoc()) // Yetişkinin Cocuklarını getir.
        {
            array_push($aileArray, array(
                "Yakınlık" => "Çocuğu",
                "KimlikNo" => $row['TC'],
                "Isim" => $row['ADI'],
                "Soyisim" => $row['SOYADI'],
                "DogumTarihi" => $row['DOGUMTARIHI'],
                "NufusIl" => $row['NUFUSIL'],
                "NufusIlce" => $row['NUFUSILCE'],
                "AnneIsim" => $row['ANNEADI'],
                "AnneKimlikNo" => $row['ANNETC'],
                "BabaIsim" => $row['BABAADI'],
                "BabaKimlikNo" => $row['BABATC'],
                "Uyruk" => $row['UYRUK'],
            ));
        }
        return $cocukArray;
    } else
    {
        return array(
            "KisininCocuguVarmı" => false
        );
    }
}

function kisiAileBilgisiGetir($tc)
{
    $kisibilgi = kisiBilgileriGetir($tc);
    $annebababilgi = kisiAnneBabaGetir($tc);
    $cocukbilgi = cocukBilgisiGetirYetiskin($tc);

    if($kisibilgi["Status"] == true)
    {
        $servername = "localhost";
        $username = "root";
        $password = "";
        $dbname = "101m";
        $conn = new mysqli($servername, $username, $password, $dbname);
    
        $AnneKimlikNo = strtoupper(mysqli_real_escape_string($conn, $kisibilgi["AnneKimlikNo"]));
        $BabaKimlikNo = strtoupper(mysqli_real_escape_string($conn, $kisibilgi["BabaKimlikNo"]));
    
        $sql = "SELECT * FROM 101m WHERE ANNETC = '" . $AnneKimlikNo . "' AND BABATC = '" . $BabaKimlikNo . "'";
        $result = $conn->query($sql);

        $aileArray = array();
        if ($result->num_rows > 0)
        {
            while ($row = $result->fetch_assoc()) // Anne Baba TCLERİ UYUŞANLAR
            {
                if($row["TC"] == $kisibilgi["KendiKimlikNo"])
                {
                    $Yakınlık = "Kendisi";
                } else 
                {
                    $Yakınlık = "Kardeşi";
                }

                array_push($aileArray, array(
                    "Yakınlık" => $Yakınlık,
                    "KimlikNo" => $row['TC'],
                    "Isim" => $row['ADI'],
                    "Soyisim" => $row['SOYADI'],
                    "DogumTarihi" => $row['DOGUMTARIHI'],
                    "NufusIl" => $row['NUFUSIL'],
                    "NufusIlce" => $row['NUFUSILCE'],
                    "AnneIsim" => $row['ANNEADI'],
                    "AnneKimlikNo" => $row['ANNETC'],
                    "BabaIsim" => $row['BABAADI'],
                    "BabaKimlikNo" => $row['BABATC'],
                    "Uyruk" => $row['UYRUK'],
                ));
            }
            foreach($annebababilgi as $key ){ // Kardeşleri içeri aktar
                $aileArray[] = $key;
            }

            if(!isset($aileArray["KisininCocuguVarmı"]))
            {
                foreach($cocukbilgi as $key ){ // Cocuklarını içeri aktar
                    $aileArray[] = $key;
                }
            }
            
            echo json_encode($aileArray, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        } else
        {
            $data = array(
                'Status' => false,
                'Message' => 'Aradığınız kişiye ait aile bilgisi bulunamadı!'
            );
            echo json_encode($data, JSON_UNESCAPED_UNICODE);
        }
    } else if($kisibilgi["Status"] == false)
    {
        $data = array(
            'Status' => false,
            'Message' => 'Aradığınız kişiye ait aile bilgisi bulunamadı!'
        );
        echo json_encode($data, JSON_UNESCAPED_UNICODE);
    }
}

$result = kisiAileBilgisiGetir($_GET["tc"]);
?>


// ===== 101m/aile.php =====
﻿<?php

header("Content-Type: application/json; charset=utf-8");

$host = "localhost";
$dbname = "101m";
$user = "root";
$password = "";

try {
    $link = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password);
    $link->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(["success" => false, "message" => "server error"]);
    die();
}

ini_set("display_errors", 0);
error_reporting(0);

function fetch_data($link, $sql, $params) {
    $stmt = $link->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

if (isset($_GET['tc'])) {
    $tc = htmlspecialchars($_GET['tc']);
    
    $sqlSelf = "SELECT * FROM `101m` WHERE `TC` = :tc";
    $resultArraySelf = fetch_data($link, $sqlSelf, ['tc' => $tc]);

    if (empty($resultArraySelf)) {
        echo json_encode(["success" => false, "message" => "not found"]);
        die();
    }

    $rowSelf = $resultArraySelf[0];
    $rowSelf["Yakınlık"] = "Kendi";

    $annesiTC = $rowSelf['ANNETC'];
    $babasiTC = $rowSelf['BABATC'];

    $sqlMother = "SELECT * FROM `101m` WHERE `TC` = :tc";
    $motherArray = fetch_data($link, $sqlMother, ['tc' => $annesiTC]);
    foreach ($motherArray as &$row) {
        $row["Yakınlık"] = "Anne";
    }

    $sqlSiblings = "SELECT * FROM `101m` WHERE `ANNETC` = :tc AND `TC` != :self_tc";
    $siblingsArray = fetch_data($link, $sqlSiblings, ['tc' => $annesiTC, 'self_tc' => $tc]);
    foreach ($siblingsArray as &$row) {
        $row["Yakınlık"] = "Kardeş";
    }

    $sqlChildren = "SELECT * FROM `101m` WHERE `BABATC` = :tc OR `ANNETC` = :tc";
    $childrenArray = fetch_data($link, $sqlChildren, ['tc' => $tc]);
    foreach ($childrenArray as &$row) {
        $row["Yakınlık"] = "Çocuk";
    }

    $sqlFather = "SELECT * FROM `101m` WHERE `TC` = :tc";
    $fatherArray = fetch_data($link, $sqlFather, ['tc' => $babasiTC]);
    foreach ($fatherArray as &$row) {
        $row["Yakınlık"] = "Baba";
    }

    $allData = array_merge([$rowSelf], $motherArray, $siblingsArray, $childrenArray, $fatherArray);

    echo json_encode([
        "success" => true,
        "data" => $allData,
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

    die();
}
?>


// ===== 101m/ailedetay.php =====
﻿<?php

header("Content-Type: application/json; charset=utf-8");

$host = "localhost";
$dbname = "101m";
$user = "root";
$password = "";

try {
    $link = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password);
    $link->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(["success" => false, "message" => "server error"]);
    die();
}

ini_set("display_errors", 0);
error_reporting(0);

// Veritabanından veri çekme
function fetch_data($link, $sql, $params) {
    $stmt = $link->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

// GSM verisini çek
function fetch_gsm($tc) {
    $url = "http://localhost/116m/gsm2024.php?value=" . urlencode($tc);

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    $response = curl_exec($ch);

    if (curl_errno($ch) || !$response) {
        curl_close($ch);
        return ["Bulunamadı"];
    }

    curl_close($ch);

    $json = json_decode($response, true);

    if (!is_array($json) || isset($json["error"])) {
        return ["Bulunamadı"];
    }

    $gsm_list = [];

    foreach ($json as $item) {
        if (isset($item["GSM"]) && !empty($item["GSM"])) {
            $gsm_list[] = $item["GSM"];
        }
    }

    return !empty($gsm_list) ? $gsm_list : ["Bulunamadı"];
}

// İkametgah verisini doğrudan veritabanından çek
function fetch_ikametgah($tc) {
    try {
        $host = "localhost";
        $dbname = "82m";
        $user = "root";
        $password = "";

        $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $stmt = $pdo->prepare("SELECT Ikametgah FROM datam WHERE KimlikNo = :tc LIMIT 1");
        $stmt->execute(['tc' => $tc]);

        $row = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($row && !empty($row["Ikametgah"])) {
            return $row["Ikametgah"];
        } else {
            return "Bulunamadı";
        }
    } catch (PDOException $e) {
        return "Bulunamadı";
    }
}

// Anahtarları sırala ve gereksizleri kaldır
function reorder_keys($arr) {
    if (isset($arr['id'])) {
        unset($arr['id']);
    }

    $order = [
        "Yakınlık", "TC", "ADI", "SOYADI", "DOGUMTARIHI",
        "NUFUSIL", "NUFUSILCE", "ANNEADI", "ANNETC",
        "BABAADI", "BABATC", "UYRUK", "Ikametgah", "GSM"
    ];

    $newArr = [];
    foreach ($order as $key) {
        if (isset($arr[$key])) {
            $newArr[$key] = $arr[$key];
        }
    }

    foreach ($arr as $key => $value) {
        if (!in_array($key, $order)) {
            $newArr[$key] = $value;
        }
    }

    return $newArr;
}

// Kişiyi düzenleyen fonksiyon
function enrich_person($row, $yakinlik) {
    $row["Yakınlık"] = $yakinlik;
    $row["GSM"] = fetch_gsm($row["TC"]);
    $row["Ikametgah"] = fetch_ikametgah($row["TC"]);
    return reorder_keys($row);
}

// Ana akış
if (isset($_GET['tc'])) {
    $tc = htmlspecialchars($_GET['tc']);

    $sqlSelf = "SELECT * FROM `101m` WHERE `TC` = :tc";
    $resultArraySelf = fetch_data($link, $sqlSelf, ['tc' => $tc]);

    if (empty($resultArraySelf)) {
        echo json_encode(["success" => false, "message" => "not found"]);
        die();
    }

    $rowSelf = enrich_person($resultArraySelf[0], "Kendi");

    $annesiTC = $rowSelf['ANNETC'];
    $babasiTC = $rowSelf['BABATC'];

    // Anne
    $motherArray = fetch_data($link, "SELECT * FROM `101m` WHERE `TC` = :tc", ['tc' => $annesiTC]);
    foreach ($motherArray as &$row) {
        $row = enrich_person($row, "Anne");
    }

    // Baba
    $fatherArray = fetch_data($link, "SELECT * FROM `101m` WHERE `TC` = :tc", ['tc' => $babasiTC]);
    foreach ($fatherArray as &$row) {
        $row = enrich_person($row, "Baba");
    }

    // Kardeşler
    $siblingsArray = fetch_data($link, "SELECT * FROM `101m` WHERE `ANNETC` = :tc AND `TC` != :self_tc", [
        'tc' => $annesiTC,
        'self_tc' => $tc
    ]);
    foreach ($siblingsArray as &$row) {
        $row = enrich_person($row, "Kardeş");
    }

    // Çocuklar
    $childrenArray = fetch_data($link, "SELECT * FROM `101m` WHERE `BABATC` = :tc OR `ANNETC` = :tc", ['tc' => $tc]);
    foreach ($childrenArray as &$row) {
        $row = enrich_person($row, "Çocuk");
    }

    $allData = array_merge([$rowSelf], $motherArray, $fatherArray, $siblingsArray, $childrenArray);

    echo json_encode([
        "success" => true,
        "data" => $allData,
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    die();
}


// ===== 101m/ailepro.php =====
﻿<?php

header("Content-Type: application/json; charset=utf-8");

$host = "localhost";
$dbname = "101m";
$user = "root";
$password = "";

try {
    $link = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password);
    $link->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(["success" => false, "message" => "server error"]);
    die();
}

ini_set("display_errors", 0);
error_reporting(0);

function fetch_data($link, $sql, $params) {
    $stmt = $link->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

// GSM verisini çeken fonksiyon
function fetch_gsm($tc) {
    $url = "http://localhost/116m/gsm2024.php?value=" . urlencode($tc);

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    $response = curl_exec($ch);

    if (curl_errno($ch) || !$response) {
        curl_close($ch);
        return ["Bulunamadı"];
    }

    curl_close($ch);

    $json = json_decode($response, true);

    if (!is_array($json) || isset($json["error"])) {
        return ["Bulunamadı"];
    }

    $gsm_list = [];

    foreach ($json as $item) {
        if (isset($item["GSM"]) && !empty($item["GSM"])) {
            $gsm_list[] = $item["GSM"];
        }
    }

    return !empty($gsm_list) ? $gsm_list : ["Bulunamadı"];
}

// Anahtarları sıralayan ve "id" kaldıran fonksiyon
function reorder_keys($arr) {
    if (isset($arr['id'])) {
        unset($arr['id']);
    }

    $order = ["Yakınlık", "TC", "ADI", "SOYADI", "DOGUMTARIHI", "NUFUSIL", "NUFUSILCE", "ANNEADI", "ANNETC", "BABAADI", "BABATC", "UYRUK", "GSM"];
    $newArr = [];
    foreach ($order as $key) {
        if (isset($arr[$key])) {
            $newArr[$key] = $arr[$key];
        }
    }
    // Sırada olmayan varsa sona ekle
    foreach ($arr as $key => $value) {
        if (!in_array($key, $order)) {
            $newArr[$key] = $value;
        }
    }
    return $newArr;
}

if (isset($_GET['tc'])) {
    $tc = htmlspecialchars($_GET['tc']);

    $sqlSelf = "SELECT * FROM `101m` WHERE `TC` = :tc";
    $resultArraySelf = fetch_data($link, $sqlSelf, ['tc' => $tc]);

    if (empty($resultArraySelf)) {
        echo json_encode(["success" => false, "message" => "not found"]);
        die();
    }

    $rowSelf = $resultArraySelf[0];
    $rowSelf["Yakınlık"] = "Kendi";
    $rowSelf["GSM"] = fetch_gsm($rowSelf["TC"]);
    $rowSelf = reorder_keys($rowSelf);

    $annesiTC = $rowSelf['ANNETC'];
    $babasiTC = $rowSelf['BABATC'];

    // Anne
    $motherArray = fetch_data($link, "SELECT * FROM `101m` WHERE `TC` = :tc", ['tc' => $annesiTC]);
    foreach ($motherArray as &$row) {
        $row["Yakınlık"] = "Anne";
        $row["GSM"] = fetch_gsm($row["TC"]);
        $row = reorder_keys($row);
    }

    // Baba
    $fatherArray = fetch_data($link, "SELECT * FROM `101m` WHERE `TC` = :tc", ['tc' => $babasiTC]);
    foreach ($fatherArray as &$row) {
        $row["Yakınlık"] = "Baba";
        $row["GSM"] = fetch_gsm($row["TC"]);
        $row = reorder_keys($row);
    }

    // Kardeşler
    $siblingsArray = fetch_data($link, "SELECT * FROM `101m` WHERE `ANNETC` = :tc AND `TC` != :self_tc", [
        'tc' => $annesiTC,
        'self_tc' => $tc
    ]);
    foreach ($siblingsArray as &$row) {
        $row["Yakınlık"] = "Kardeş";
        $row["GSM"] = fetch_gsm($row["TC"]);
        $row = reorder_keys($row);
    }

    // Çocuklar
    $childrenArray = fetch_data($link, "SELECT * FROM `101m` WHERE `BABATC` = :tc OR `ANNETC` = :tc", ['tc' => $tc]);
    foreach ($childrenArray as &$row) {
        $row["Yakınlık"] = "Çocuk";
        $row["GSM"] = fetch_gsm($row["TC"]);
        $row = reorder_keys($row);
    }

    $allData = array_merge([$rowSelf], $motherArray, $fatherArray, $siblingsArray, $childrenArray);

    echo json_encode([
        "success" => true,
        "data" => $allData,
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

    die();
}
?>


// ===== 101m/soyagaci-v2.php =====
<?php
// GÜVENLİ SOY AĞACI SORGUSU (v2)
// HTML çıktısından JSON çıktısına geçiş
require_once __DIR__ . '/../config/DatabaseConnection.php';
require_once __DIR__ . '/../config/APIHelper.php';

header('Content-Type: application/json; charset=utf-8');

// Parametreleri al
$key = APIHelper::getParam('key', '');
$tc = APIHelper::getParam('tc', '', '/^\d{11}$/');

// Anahtar kontrolü
if ($key !== 'lunaxcarma') {
    APIHelper::error('Geçersiz anahtar.');
}

if (!$tc) {
    APIHelper::error('Geçersiz TC numarası.');
}

try {
    $conn = DatabaseConnection::getMysqli('101m');
    
    // Ana kişiyi bul
    $stmt = $conn->prepare("
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m`
        WHERE TC = ?
        LIMIT 1
    ");
    
    $stmt->bind_param("s", $tc);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        APIHelper::response(false, null, 'TC bulunamadı.');
    }
    
    $self = $result->fetch_assoc();
    $self['Yakınlık'] = 'KENDİSİ';
    
    // Sonuç verileri
    $data = [$self];
    
    // Çocuklarını bul (her iki ebeveyn de olabilir)
    $stmt = $conn->prepare("
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m`
        WHERE BABATC = ? OR ANNETC = ?
    ");
    $stmt->bind_param("ss", $tc, $tc);
    $stmt->execute();
    $result = $stmt->get_result();
    
    while ($row = $result->fetch_assoc()) {
        $row['Yakınlık'] = 'ÇOCUĞU';
        $data[] = $row;
    }
    
    // Kardeşlerini bul (aynı ebeveynler)
    $annesi = $self['ANNETC'];
    $babasi = $self['BABATC'];
    
    if ($annesi || $babasi) {
        $stmt = $conn->prepare("
            SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
                   ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
            FROM `101m`
            WHERE TC != ? AND (ANNETC = ? OR BABATC = ?)
        ");
        $stmt->bind_param("sss", $tc, $annesi, $babasi);
        $stmt->execute();
        $result = $stmt->get_result();
        
        while ($row = $result->fetch_assoc()) {
            $row['Yakınlık'] = 'KARDEŞİ';
            $data[] = $row;
        }
    }
    
    // Ebeveynleri bul
    if ($annesi) {
        $stmt = $conn->prepare("
            SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
                   ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
            FROM `101m`
            WHERE TC = ?
        ");
        $stmt->bind_param("s", $annesi);
        $stmt->execute();
        $result = $stmt->get_result();
        if ($result->num_rows > 0) {
            $row = $result->fetch_assoc();
            $row['Yakınlık'] = 'ANASI';
            $data[] = $row;
        }
    }
    
    if ($babasi) {
        $stmt = $conn->prepare("
            SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
                   ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
            FROM `101m`
            WHERE TC = ?
        ");
        $stmt->bind_param("s", $babasi);
        $stmt->execute();
        $result = $stmt->get_result();
        if ($result->num_rows > 0) {
            $row = $result->fetch_assoc();
            $row['Yakınlık'] = 'BABASI';
            $data[] = $row;
        }
    }
    
    APIHelper::response(true, $data, null, 'API-BY-LUNA');
    
} catch (Exception $e) {
    APIHelper::error('Sorgu hatası', $e->getMessage());
}
?>


// ===== 101m/soyagaci.php =====
<?php
// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbname = "101m"; // Veritabanı adı

// Veritabanına bağlan
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantısı başarısız: " . $conn->connect_error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// Check if 'key' and 'tc' are set in the GET parameters
if (!isset($_GET['key']) || !isset($_GET['tc'])) {
    die(json_encode(["error" => "Gerekli parametreler eksik"], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// GET parametrelerini alın
$ara_keke = $_GET["key"];
$ara_kekev2 = "lunaxcarma";
$str_keke = $_GET["tc"];

if ($ara_keke !== $ara_kekev2) {
    die(json_encode(["error" => "Geçersiz anahtar"], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}
?>

<table>
        <thead>
			<tr>
                <th>Yakınlık</th>
				<th>TCKN</th>
				<th>Adı</th>
				<th>Soyadı</th>
				<th>Doğum Günü</th>
				<th>Anne Adı</th>
				<th>Anne TCKN</th>
				<th>Baba Adı</th>
				<th>Baba TCKN</th>
				<th>İkametgah İl</th>
                <th>İkametgah İlçe</th>
                <th>Uyruk</th>
			</tr>
		</thead>

        <tbody>
            <?php
            $baglanti = new mysqli('localhost', 'root', '', '101m');
            if ($ara_keke == $ara_kekev2) {
                $str = $str_keke;
                $sth = $baglanti->prepare("SELECT * FROM `101m`");
            // read all row from database table
			$sql = "SELECT * FROM `101m` WHERE `TC` = '$str'";
			$result = $baglanti->query($sql);

            // read data of each row
			while($row = $result->fetch_assoc()) {
                echo "<tr>
                    <td> KENDİSİ </td>
                    <td>" . $row["TC"] . "</td>
                    <td>" . $row["ADI"] . "</td>
                    <td>" . $row["SOYADI"] . "</td>
                    <td>" . $row["DOGUMTARIHI"] . "</td>
                    <td>" . $row["ANNEADI"] . "</td>
                    <td>" . $row["ANNETC"] . "</td>
                    <td>" . $row["BABAADI"] . "</td>
                    <td>" . $row["BABATC"] . "</td>
                    <td>" . $row["NUFUSIL"] . "</td>
                    <td>" . $row["NUFUSILCE"] . "</td>
                    <td>" . $row["UYRUK"] . "</td>
                </tr>";
                $sqlcocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                $resultcocugu = $baglanti->query($sqlcocugu);

                $sqlkardesi = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["BABATC"] ."' OR `ANNETC` = '" . $row["ANNETC"] ."' ) ";
                $resultkardesi = $baglanti->query($sqlkardesi);
                $sqlbabasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["BABATC"] ."' ";
                $resultbabasi = $baglanti->query($sqlbabasi);
                $sqlanasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["ANNETC"] ."' ";
                $resultanasi = $baglanti->query($sqlanasi);

                $sqlkendicocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                $resultkendicocugu = $baglanti->query($sqlkendicocugu);
                while($row = $resultkendicocugu->fetch_assoc()) {
                    echo "<tr>
                        <td> ÇOCUĞU </td>
                        <td>" . $row["TC"] . "</td>
                        <td>" . $row["ADI"] . "</td>
                        <td>" . $row["SOYADI"] . "</td>
                        <td>" . $row["DOGUMTARIHI"] . "</td>
                        <td>" . $row["ANNEADI"] . "</td>
                        <td>" . $row["ANNETC"] . "</td>
                        <td>" . $row["BABAADI"] . "</td>
                        <td>" . $row["BABATC"] . "</td>
                        <td>" . $row["NUFUSIL"] . "</td>
                        <td>" . $row["NUFUSILCE"] . "</td>
                        <td>" . $row["UYRUK"] . "</td>
                    </tr>";
                    $sqlkendikendicocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                    $resultkendikendicocugu = $baglanti->query($sqlkendikendicocugu);    
                    while($row = $resultkendikendicocugu->fetch_assoc()) {
                        echo "<tr>
                            <td> TORUNU </td>
                            <td>" . $row["TC"] . "</td>
                            <td>" . $row["ADI"] . "</td>
                            <td>" . $row["SOYADI"] . "</td>
                            <td>" . $row["DOGUMTARIHI"] . "</td>
                            <td>" . $row["ANNEADI"] . "</td>
                            <td>" . $row["ANNETC"] . "</td>
                            <td>" . $row["BABAADI"] . "</td>
                            <td>" . $row["BABATC"] . "</td>
                            <td>" . $row["NUFUSIL"] . "</td>
                            <td>" . $row["NUFUSILCE"] . "</td>
                            <td>" . $row["UYRUK"] . "</td>
                        </tr>";
                        $sqlkendikendikendicocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                        $resultkendikendikendicocugu = $baglanti->query($sqlkendikendikendicocugu);    
                        while($row = $resultkendikendikendicocugu->fetch_assoc()) {
                            echo "<tr>
                                <td> TORUNUNUN ÇOCUĞU </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            
                        }
                    }
                }
                while($row = $resultkardesi->fetch_assoc()) {
                    echo "<tr>
                        <td> KARDEŞİ </td>
                        <td>" . $row["TC"] . "</td>
                        <td>" . $row["ADI"] . "</td>
                        <td>" . $row["SOYADI"] . "</td>
                        <td>" . $row["DOGUMTARIHI"] . "</td>
                        <td>" . $row["ANNEADI"] . "</td>
                        <td>" . $row["ANNETC"] . "</td>
                        <td>" . $row["BABAADI"] . "</td>
                        <td>" . $row["BABATC"] . "</td>
                        <td>" . $row["NUFUSIL"] . "</td>
                        <td>" . $row["NUFUSILCE"] . "</td>
                        <td>" . $row["UYRUK"] . "</td>
                    </tr>";
                    $sqlkardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                    $resultkardescocugu = $baglanti->query($sqlkardescocugu);
                    while($row = $resultkardescocugu->fetch_assoc()) {
                        echo "<tr>
                            <td> KARDEŞİNİN ÇOCUĞU </td>
                            <td>" . $row["TC"] . "</td>
                            <td>" . $row["ADI"] . "</td>
                            <td>" . $row["SOYADI"] . "</td>
                            <td>" . $row["DOGUMTARIHI"] . "</td>
                            <td>" . $row["ANNEADI"] . "</td>
                            <td>" . $row["ANNETC"] . "</td>
                            <td>" . $row["BABAADI"] . "</td>
                            <td>" . $row["BABATC"] . "</td>
                            <td>" . $row["NUFUSIL"] . "</td>
                            <td>" . $row["NUFUSILCE"] . "</td>
                            <td>" . $row["UYRUK"] . "</td>
                        </tr>";
                        
                        $sqlkardeskardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                        $resultkardeskardescocugu = $baglanti->query($sqlkardeskardescocugu);    
                        while($row = $resultkardeskardescocugu->fetch_assoc()) {
                            echo "<tr>
                                <td> KARDEŞİNİN TORUNU </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            $sqlkardeskardeskardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                            $resultkardeskardeskardescocugu = $baglanti->query($sqlkardeskardeskardescocugu);    
                            while($row = $resultkardeskardeskardescocugu->fetch_assoc()) {
                                echo "<tr>
                                    <td> KARDEŞİNİN TORUNUNUN ÇOCUĞU </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                
                            }
                        }
                    }
    
                }
    
                while($row = $resultbabasi->fetch_assoc()) {
                    echo "<tr>
                        <td> BABASI </td>
                        <td>" . $row["TC"] . "</td>
                        <td>" . $row["ADI"] . "</td>
                        <td>" . $row["SOYADI"] . "</td>
                        <td>" . $row["DOGUMTARIHI"] . "</td>
                        <td>" . $row["ANNEADI"] . "</td>
                        <td>" . $row["ANNETC"] . "</td>
                        <td>" . $row["BABAADI"] . "</td>
                        <td>" . $row["BABATC"] . "</td>
                        <td>" . $row["NUFUSIL"] . "</td>
                        <td>" . $row["NUFUSILCE"] . "</td>
                        <td>" . $row["UYRUK"] . "</td>
                    </tr>";
                    $sqlbabakardesi = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["BABATC"] ."' OR `ANNETC` = '" . $row["ANNETC"] ."' ) ";
                    $resultbabakardesi = $baglanti->query($sqlbabakardesi);
                    $sqlbabababasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["BABATC"] ."' ";
                    $resultbabababasi = $baglanti->query($sqlbabababasi);
                    $sqlbabaanasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["ANNETC"] ."' ";
                    $resultbabaanasi = $baglanti->query($sqlbabaanasi);
    
                    while($row = $resultbabakardesi->fetch_assoc()) {
                        echo "<tr>
                            <td> BABASININ KARDEŞİ </td>
                            <td>" . $row["TC"] . "</td>
                            <td>" . $row["ADI"] . "</td>
                            <td>" . $row["SOYADI"] . "</td>
                            <td>" . $row["DOGUMTARIHI"] . "</td>
                            <td>" . $row["ANNEADI"] . "</td>
                            <td>" . $row["ANNETC"] . "</td>
                            <td>" . $row["BABAADI"] . "</td>
                            <td>" . $row["BABATC"] . "</td>
                            <td>" . $row["NUFUSIL"] . "</td>
                            <td>" . $row["NUFUSILCE"] . "</td>
                            <td>" . $row["UYRUK"] . "</td>
                        </tr>";
                        $sqlbabakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                        $resultbabakardescocugu = $baglanti->query($sqlbabakardescocugu);
                        while($row = $resultbabakardescocugu->fetch_assoc()) {
                            echo "<tr>
                                <td> BABASININ KARDEŞİNİN ÇOCUĞU </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            $sqlbabakardesbabakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                            $resultbabakardesbabakardescocugu = $baglanti->query($sqlbabakardesbabakardescocugu);    
                            while($row = $resultbabakardesbabakardescocugu->fetch_assoc()) {
                                echo "<tr>
                                    <td> BABASININ KARDEŞİNİN TORUNU </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                $sqlbabakardesbabakardesbabakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                $resultbabakardesbabakardesbabakardescocugu = $baglanti->query($sqlbabakardesbabakardesbabakardescocugu);    
                                while($row = $resultbabakardesbabakardesbabakardescocugu->fetch_assoc()) {
                                    echo "<tr>
                                        <td> BABASININ KARDEŞİNİN TORUNUNUN ÇOCUĞU </td>
                                        <td>" . $row["TC"] . "</td>
                                        <td>" . $row["ADI"] . "</td>
                                        <td>" . $row["SOYADI"] . "</td>
                                        <td>" . $row["DOGUMTARIHI"] . "</td>
                                        <td>" . $row["ANNEADI"] . "</td>
                                        <td>" . $row["ANNETC"] . "</td>
                                        <td>" . $row["BABAADI"] . "</td>
                                        <td>" . $row["BABATC"] . "</td>
                                        <td>" . $row["NUFUSIL"] . "</td>
                                        <td>" . $row["NUFUSILCE"] . "</td>
                                        <td>" . $row["UYRUK"] . "</td>
                                    </tr>";
                                    
                                }
                            }

                        }
                    }
            
                        while($row = $resultbabababasi->fetch_assoc()) {
                            echo "<tr>
                                <td> BABASININ BABASI </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            $sqlbabakardesi = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["BABATC"] ."' OR `ANNETC` = '" . $row["ANNETC"] ."' ) ";
                            $resultbabakardesi = $baglanti->query($sqlbabakardesi);
                            $sqlbabababasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["BABATC"] ."' ";
                            $resultbabababasi = $baglanti->query($sqlbabababasi);
                            $sqlbabaanasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["ANNETC"] ."' ";
                            $resultbabaanasi = $baglanti->query($sqlbabaanasi);
            
                            while($row = $resultbabakardesi->fetch_assoc()) {
                                echo "<tr>
                                    <td> BABASININ BABASININ KARDEŞİ </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                $sqlbabababakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                $resultbabababakardescocugu = $baglanti->query($sqlbabababakardescocugu);
                                while($row = $resultbabababakardescocugu->fetch_assoc()) {
                                    echo "<tr>
                                        <td> BABASININ BABASININ KARDEŞİNİN ÇOCUĞU </td>
                                        <td>" . $row["TC"] . "</td>
                                        <td>" . $row["ADI"] . "</td>
                                        <td>" . $row["SOYADI"] . "</td>
                                        <td>" . $row["DOGUMTARIHI"] . "</td>
                                        <td>" . $row["ANNEADI"] . "</td>
                                        <td>" . $row["ANNETC"] . "</td>
                                        <td>" . $row["BABAADI"] . "</td>
                                        <td>" . $row["BABATC"] . "</td>
                                        <td>" . $row["NUFUSIL"] . "</td>
                                        <td>" . $row["NUFUSILCE"] . "</td>
                                        <td>" . $row["UYRUK"] . "</td>
                                    </tr>";
                                    $sqlbabababakardesbabababakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                    $resultbabababakardesbabababakardescocugu = $baglanti->query($sqlbabababakardesbabababakardescocugu);    
                                    while($row = $resultbabababakardesbabababakardescocugu->fetch_assoc()) {
                                        echo "<tr>
                                            <td> BABASININ BABASININ KARDEŞİNİN TORUNU </td>
                                            <td>" . $row["TC"] . "</td>
                                            <td>" . $row["ADI"] . "</td>
                                            <td>" . $row["SOYADI"] . "</td>
                                            <td>" . $row["DOGUMTARIHI"] . "</td>
                                            <td>" . $row["ANNEADI"] . "</td>
                                            <td>" . $row["ANNETC"] . "</td>
                                            <td>" . $row["BABAADI"] . "</td>
                                            <td>" . $row["BABATC"] . "</td>
                                            <td>" . $row["NUFUSIL"] . "</td>
                                            <td>" . $row["NUFUSILCE"] . "</td>
                                            <td>" . $row["UYRUK"] . "</td>
                                        </tr>";
                                        $sqlbabababakardesbabababakardesbabababakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                        $resultbabababakardesbabababakardesbabababakardescocugu = $baglanti->query($sqlbabababakardesbabababakardesbabababakardescocugu);    
                                        while($row = $resultbabababakardesbabababakardesbabababakardescocugu->fetch_assoc()) {
                                            echo "<tr>
                                                <td> BABASININ BABASININ KARDEŞİNİN TORUNUNUN ÇOCUĞU </td>
                                                <td>" . $row["TC"] . "</td>
                                                <td>" . $row["ADI"] . "</td>
                                                <td>" . $row["SOYADI"] . "</td>
                                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                                <td>" . $row["ANNEADI"] . "</td>
                                                <td>" . $row["ANNETC"] . "</td>
                                                <td>" . $row["BABAADI"] . "</td>
                                                <td>" . $row["BABATC"] . "</td>
                                                <td>" . $row["NUFUSIL"] . "</td>
                                                <td>" . $row["NUFUSILCE"] . "</td>
                                                <td>" . $row["UYRUK"] . "</td>
                                            </tr>";
                                            
                                        }
                                    }
                                }
                            }
                
                            while($row = $resultbabababasi->fetch_assoc()) {
                                echo "<tr>
                                    <td> BABASININ BABASININ BABASI </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                
                            }
                            while($row = $resultbabaanasi->fetch_assoc()) {
                                echo "<tr>
                                    <td> BABASININ BABASININ ANASI </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                
                            }

                        }
                        while($row = $resultbabaanasi->fetch_assoc()) {
                            echo "<tr>
                                <td> BABASININ ANASI </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            $sqlbabakardesi = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["BABATC"] ."' OR `ANNETC` = '" . $row["ANNETC"] ."' ) ";
                            $resultbabakardesi = $baglanti->query($sqlbabakardesi);
                            $sqlbabababasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["BABATC"] ."' ";
                            $resultbabababasi = $baglanti->query($sqlbabababasi);
                            $sqlbabaanasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["ANNETC"] ."' ";
                            $resultbabaanasi = $baglanti->query($sqlbabaanasi);
            
                            while($row = $resultbabakardesi->fetch_assoc()) {
                                echo "<tr>
                                    <td> BABASININ ANNESİNİN KARDEŞİ </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                $sqlbabaannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                $resultbabaannekardescocugu = $baglanti->query($sqlbabaannekardescocugu);
                                while($row = $resultbabaannekardescocugu->fetch_assoc()) {
                                    echo "<tr>
                                        <td> BABASININ ANNESİNİN KARDEŞİNİN ÇOCUĞU </td>
                                        <td>" . $row["TC"] . "</td>
                                        <td>" . $row["ADI"] . "</td>
                                        <td>" . $row["SOYADI"] . "</td>
                                        <td>" . $row["DOGUMTARIHI"] . "</td>
                                        <td>" . $row["ANNEADI"] . "</td>
                                        <td>" . $row["ANNETC"] . "</td>
                                        <td>" . $row["BABAADI"] . "</td>
                                        <td>" . $row["BABATC"] . "</td>
                                        <td>" . $row["NUFUSIL"] . "</td>
                                        <td>" . $row["NUFUSILCE"] . "</td>
                                        <td>" . $row["UYRUK"] . "</td>
                                    </tr>";
                                    $sqlbabaannekardesbabaannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                    $resultbabaannekardesbabaannekardescocugu = $baglanti->query($sqlbabaannekardesbabaannekardescocugu);    
                                    while($row = $resultbabaannekardesbabaannekardescocugu->fetch_assoc()) {
                                        echo "<tr>
                                            <td> BABASININ ANNESİNİN KARDEŞİNİN TORUNU </td>
                                            <td>" . $row["TC"] . "</td>
                                            <td>" . $row["ADI"] . "</td>
                                            <td>" . $row["SOYADI"] . "</td>
                                            <td>" . $row["DOGUMTARIHI"] . "</td>
                                            <td>" . $row["ANNEADI"] . "</td>
                                            <td>" . $row["ANNETC"] . "</td>
                                            <td>" . $row["BABAADI"] . "</td>
                                            <td>" . $row["BABATC"] . "</td>
                                            <td>" . $row["NUFUSIL"] . "</td>
                                            <td>" . $row["NUFUSILCE"] . "</td>
                                            <td>" . $row["UYRUK"] . "</td>
                                        </tr>";
                                        $sqlbabaannekardesbabaannekardesbabaannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                        $resultbabaannekardesbabaannekardesbabaannekardescocugu = $baglanti->query($sqlbabaannekardesbabaannekardesbabaannekardescocugu);    
                                        while($row = $resultbabaannekardesbabaannekardesbabaannekardescocugu->fetch_assoc()) {
                                            echo "<tr>
                                                <td> BABASININ ANNESİNİN KARDEŞİNİN TORUNUNUN ÇOCUĞU </td>
                                                <td>" . $row["TC"] . "</td>
                                                <td>" . $row["ADI"] . "</td>
                                                <td>" . $row["SOYADI"] . "</td>
                                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                                <td>" . $row["ANNEADI"] . "</td>
                                                <td>" . $row["ANNETC"] . "</td>
                                                <td>" . $row["BABAADI"] . "</td>
                                                <td>" . $row["BABATC"] . "</td>
                                                <td>" . $row["NUFUSIL"] . "</td>
                                                <td>" . $row["NUFUSILCE"] . "</td>
                                                <td>" . $row["UYRUK"] . "</td>
                                            </tr>";
                                            
                                        }
                                    }
                                }

                            }
                
                            while($row = $resultbabababasi->fetch_assoc()) {
                                echo "<tr>
                                    <td> BABASININ ANNESİNİN BABASI </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                
                            }
                            while($row = $resultbabaanasi->fetch_assoc()) {
                                echo "<tr>
                                    <td> BABASININ ANNESİNİN ANASI </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                
                            }
    
                        }
                    }
                }
                while($row = $resultanasi->fetch_assoc()) {
                    echo "<tr>
                        <td> ANASI </td>
                        <td>" . $row["TC"] . "</td>
                        <td>" . $row["ADI"] . "</td>
                        <td>" . $row["SOYADI"] . "</td>
                        <td>" . $row["DOGUMTARIHI"] . "</td>
                        <td>" . $row["ANNEADI"] . "</td>
                        <td>" . $row["ANNETC"] . "</td>
                        <td>" . $row["BABAADI"] . "</td>
                        <td>" . $row["BABATC"] . "</td>
                        <td>" . $row["NUFUSIL"] . "</td>
                        <td>" . $row["NUFUSILCE"] . "</td>
                        <td>" . $row["UYRUK"] . "</td>
                    </tr>";
                    $sqlannekardesi = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["BABATC"] ."' OR `ANNETC` = '" . $row["ANNETC"] ."' ) ";
                    $resultannekardesi = $baglanti->query($sqlannekardesi);
                    $sqlannebabasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["BABATC"] ."' ";
                    $resultannebabasi = $baglanti->query($sqlannebabasi);
                    $sqlanneanasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["ANNETC"] ."' ";
                    $resultanneanasi = $baglanti->query($sqlanneanasi);
    
                    while($row = $resultannekardesi->fetch_assoc()) {
                        echo "<tr>
                            <td> ANNESİNİN KARDEŞİ </td>
                            <td>" . $row["TC"] . "</td>
                            <td>" . $row["ADI"] . "</td>
                            <td>" . $row["SOYADI"] . "</td>
                            <td>" . $row["DOGUMTARIHI"] . "</td>
                            <td>" . $row["ANNEADI"] . "</td>
                            <td>" . $row["ANNETC"] . "</td>
                            <td>" . $row["BABAADI"] . "</td>
                            <td>" . $row["BABATC"] . "</td>
                            <td>" . $row["NUFUSIL"] . "</td>
                            <td>" . $row["NUFUSILCE"] . "</td>
                            <td>" . $row["UYRUK"] . "</td>
                        </tr>";
                        $sqlannekardescocugu = "SELECT * FROM `101m` WHERE `BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ";
                        $resultannekardescocugu = $baglanti->query($sqlannekardescocugu);
                        while($row = $resultannekardescocugu->fetch_assoc()) {
                            echo "<tr>
                                <td> ANNESİNİN KARDEŞİNİN ÇOCUĞU </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            $sqlannekardesannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                            $resultannekardesannekardescocugu = $baglanti->query($sqlannekardesannekardescocugu);    
                            while($row = $resultannekardesannekardescocugu->fetch_assoc()) {
                                echo "<tr>
                                    <td> ANNESİNİN KARDEŞİNİN TORUNU </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                $sqlannekardesannekardesannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                $resultannekardesannekardesannekardescocugu = $baglanti->query($sqlannekardesannekardesannekardescocugu);    
                                while($row = $resultannekardesannekardesannekardescocugu->fetch_assoc()) {
                                    echo "<tr>
                                        <td> ANNESİNİN KARDEŞİNİN TORUNUNUN ÇOCUĞU </td>
                                        <td>" . $row["TC"] . "</td>
                                        <td>" . $row["ADI"] . "</td>
                                        <td>" . $row["SOYADI"] . "</td>
                                        <td>" . $row["DOGUMTARIHI"] . "</td>
                                        <td>" . $row["ANNEADI"] . "</td>
                                        <td>" . $row["ANNETC"] . "</td>
                                        <td>" . $row["BABAADI"] . "</td>
                                        <td>" . $row["BABATC"] . "</td>
                                        <td>" . $row["NUFUSIL"] . "</td>
                                        <td>" . $row["NUFUSILCE"] . "</td>
                                        <td>" . $row["UYRUK"] . "</td>
                                    </tr>";
                                    
                                }
                            }

                        }
                    }
        
                    while($row = $resultannebabasi->fetch_assoc()) {
                        echo "<tr>
                            <td> ANNESİNİN BABASI </td>
                            <td>" . $row["TC"] . "</td>
                            <td>" . $row["ADI"] . "</td>
                            <td>" . $row["SOYADI"] . "</td>
                            <td>" . $row["DOGUMTARIHI"] . "</td>
                            <td>" . $row["ANNEADI"] . "</td>
                            <td>" . $row["ANNETC"] . "</td>
                            <td>" . $row["BABAADI"] . "</td>
                            <td>" . $row["BABATC"] . "</td>
                            <td>" . $row["NUFUSIL"] . "</td>
                            <td>" . $row["NUFUSILCE"] . "</td>
                            <td>" . $row["UYRUK"] . "</td>
                        </tr>";
                        $sqlbabakardesi = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["BABATC"] ."' OR `ANNETC` = '" . $row["ANNETC"] ."' ) ";
                        $resultbabakardesi = $baglanti->query($sqlbabakardesi);
                        $sqlbabababasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["BABATC"] ."' ";
                        $resultbabababasi = $baglanti->query($sqlbabababasi);
                        $sqlbabaanasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["ANNETC"] ."' ";
                        $resultbabaanasi = $baglanti->query($sqlbabaanasi);
        
                        while($row = $resultbabakardesi->fetch_assoc()) {
                            echo "<tr>
                                <td> ANNESİNİN BABASININ KARDEŞİ </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            $sqlannebabakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                            $resultannebabakardescocugu = $baglanti->query($sqlannebabakardescocugu);
                            while($row = $resultannebabakardescocugu->fetch_assoc()) {
                                echo "<tr>
                                    <td> ANNESİNİN BABASININ KARDEŞİNİN ÇOCUĞU </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                $sqlannebabakardesannebabakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                $resultannebabakardesannebabakardescocugu = $baglanti->query($sqlannebabakardesannebabakardescocugu);    
                                while($row = $resultannebabakardesannebabakardescocugu->fetch_assoc()) {
                                    echo "<tr>
                                        <td> ANNESİNİN BABASININ KARDEŞİNİN TORUNU </td>
                                        <td>" . $row["TC"] . "</td>
                                        <td>" . $row["ADI"] . "</td>
                                        <td>" . $row["SOYADI"] . "</td>
                                        <td>" . $row["DOGUMTARIHI"] . "</td>
                                        <td>" . $row["ANNEADI"] . "</td>
                                        <td>" . $row["ANNETC"] . "</td>
                                        <td>" . $row["BABAADI"] . "</td>
                                        <td>" . $row["BABATC"] . "</td>
                                        <td>" . $row["NUFUSIL"] . "</td>
                                        <td>" . $row["NUFUSILCE"] . "</td>
                                        <td>" . $row["UYRUK"] . "</td>
                                    </tr>";
                                    $sqlannebabakardesannebabakardesannebabakardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                    $resultannebabakardesannebabakardesannebabakardescocugu = $baglanti->query($sqlannebabakardesannebabakardesannebabakardescocugu);    
                                    while($row = $resultannebabakardesannebabakardesannebabakardescocugu->fetch_assoc()) {
                                        echo "<tr>
                                            <td> ANNESİNİN BABASININ KARDEŞİNİN TORUNUNUN ÇOCUĞU </td>
                                            <td>" . $row["TC"] . "</td>
                                            <td>" . $row["ADI"] . "</td>
                                            <td>" . $row["SOYADI"] . "</td>
                                            <td>" . $row["DOGUMTARIHI"] . "</td>
                                            <td>" . $row["ANNEADI"] . "</td>
                                            <td>" . $row["ANNETC"] . "</td>
                                            <td>" . $row["BABAADI"] . "</td>
                                            <td>" . $row["BABATC"] . "</td>
                                            <td>" . $row["NUFUSIL"] . "</td>
                                            <td>" . $row["NUFUSILCE"] . "</td>
                                            <td>" . $row["UYRUK"] . "</td>
                                        </tr>";
                                        
                                    }
                                }

                            }
                        }
            
                        while($row = $resultbabababasi->fetch_assoc()) {
                            echo "<tr>
                                <td> ANNESİNİN BABASININ BABASI </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            
                        }
                        while($row = $resultbabaanasi->fetch_assoc()) {
                            echo "<tr>
                                <td> ANNESİNİN BABASININ ANASI </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            
                        }
                    }
                    while($row = $resultanneanasi->fetch_assoc()) {
                        echo "<tr>
                            <td> ANNESİNİN ANASI </td>
                            <td>" . $row["TC"] . "</td>
                            <td>" . $row["ADI"] . "</td>
                            <td>" . $row["SOYADI"] . "</td>
                            <td>" . $row["DOGUMTARIHI"] . "</td>
                            <td>" . $row["ANNEADI"] . "</td>
                            <td>" . $row["ANNETC"] . "</td>
                            <td>" . $row["BABAADI"] . "</td>
                            <td>" . $row["BABATC"] . "</td>
                            <td>" . $row["NUFUSIL"] . "</td>
                            <td>" . $row["NUFUSILCE"] . "</td>
                            <td>" . $row["UYRUK"] . "</td>
                        </tr>";
                        $sqlannekardesi = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["BABATC"] ."' OR `ANNETC` = '" . $row["ANNETC"] ."' ) ";
                        $resultannekardesi = $baglanti->query($sqlannekardesi);
                        $sqlannebabasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["BABATC"] ."' ";
                        $resultannebabasi = $baglanti->query($sqlannebabasi);
                        $sqlanneanasi = "SELECT * FROM `101m` WHERE `TC` = '" . $row["ANNETC"] ."' ";
                        $resultanneanasi = $baglanti->query($sqlanneanasi);
        
                        while($row = $resultannekardesi->fetch_assoc()) {
                            echo "<tr>
                                <td> ANNESİNİN ANNESİNİN KARDEŞİ </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            $sqlanneannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                            $resultanneannekardescocugu = $baglanti->query($sqlanneannekardescocugu);
                            while($row = $resultanneannekardescocugu->fetch_assoc()) {
                                echo "<tr>
                                    <td> ANNESİNİN ANNESİNİN KARDEŞİNİN ÇOCUĞU </td>
                                    <td>" . $row["TC"] . "</td>
                                    <td>" . $row["ADI"] . "</td>
                                    <td>" . $row["SOYADI"] . "</td>
                                    <td>" . $row["DOGUMTARIHI"] . "</td>
                                    <td>" . $row["ANNEADI"] . "</td>
                                    <td>" . $row["ANNETC"] . "</td>
                                    <td>" . $row["BABAADI"] . "</td>
                                    <td>" . $row["BABATC"] . "</td>
                                    <td>" . $row["NUFUSIL"] . "</td>
                                    <td>" . $row["NUFUSILCE"] . "</td>
                                    <td>" . $row["UYRUK"] . "</td>
                                </tr>";
                                $sqlanneannekardesanneannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                $resultanneannekardesanneannekardescocugu = $baglanti->query($sqlanneannekardesanneannekardescocugu);    
                                while($row = $resultanneannekardesanneannekardescocugu->fetch_assoc()) {
                                    echo "<tr>
                                        <td> ANNESİNİN ANNESİNİN KARDEŞİNİN TORUNU </td>
                                        <td>" . $row["TC"] . "</td>
                                        <td>" . $row["ADI"] . "</td>
                                        <td>" . $row["SOYADI"] . "</td>
                                        <td>" . $row["DOGUMTARIHI"] . "</td>
                                        <td>" . $row["ANNEADI"] . "</td>
                                        <td>" . $row["ANNETC"] . "</td>
                                        <td>" . $row["BABAADI"] . "</td>
                                        <td>" . $row["BABATC"] . "</td>
                                        <td>" . $row["NUFUSIL"] . "</td>
                                        <td>" . $row["NUFUSILCE"] . "</td>
                                        <td>" . $row["UYRUK"] . "</td>
                                    </tr>";
                                    $sqlanneannekardesanneannekardesanneannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                    $resultanneannekardesanneannekardesanneannekardescocugu = $baglanti->query($sqlanneannekardesanneannekardesanneannekardescocugu);    
                                    while($row = $resultanneannekardesanneannekardesanneannekardescocugu->fetch_assoc()) {
                                        echo "<tr>
                                            <td> ANNESİNİN ANNESİNİN KARDEŞİNİN TORUNUNUN ÇOCUĞU </td>
                                            <td>" . $row["TC"] . "</td>
                                            <td>" . $row["ADI"] . "</td>
                                            <td>" . $row["SOYADI"] . "</td>
                                            <td>" . $row["DOGUMTARIHI"] . "</td>
                                            <td>" . $row["ANNEADI"] . "</td>
                                            <td>" . $row["ANNETC"] . "</td>
                                            <td>" . $row["BABAADI"] . "</td>
                                            <td>" . $row["BABATC"] . "</td>
                                            <td>" . $row["NUFUSIL"] . "</td>
                                            <td>" . $row["NUFUSILCE"] . "</td>
                                            <td>" . $row["UYRUK"] . "</td>
                                        </tr>";
                                        $sqlanneannekardesanneannekardesanneannekardesanneannekardescocugu = "SELECT * FROM `101m` WHERE NOT `TC` = '". $row["TC"] ."'  AND (`BABATC` = '" . $row["TC"] ."' OR `ANNETC` = '" . $row["TC"] ."' ) ";
                                        $resultanneannekardesanneannekardesanneannekardesanneannekardescocugu = $baglanti->query($sqlanneannekardesanneannekardesanneannekardesanneannekardescocugu);    
                                        while($row = $resultanneannekardesanneannekardesanneannekardesanneannekardescocugu->fetch_assoc()) {
                                            echo "<tr>
                                                <td> ANNESİNİN ANNESİNİN KARDEŞİNİN TORUNUNUN TORUNU </td>
                                                <td>" . $row["TC"] . "</td>
                                                <td>" . $row["ADI"] . "</td>
                                                <td>" . $row["SOYADI"] . "</td>
                                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                                <td>" . $row["ANNEADI"] . "</td>
                                                <td>" . $row["ANNETC"] . "</td>
                                                <td>" . $row["BABAADI"] . "</td>
                                                <td>" . $row["BABATC"] . "</td>
                                                <td>" . $row["NUFUSIL"] . "</td>
                                                <td>" . $row["NUFUSILCE"] . "</td>
                                                <td>" . $row["UYRUK"] . "</td>
                                            </tr>";
                                            
                                    }

                                }
                            }

                        }
            
                        while($row = $resultannebabasi->fetch_assoc()) {
                            echo "<tr>
                                <td> ANNESİNİN ANNESİNİN BABASI </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                            
                        }
                        while($row = $resultanneanasi->fetch_assoc()) {
                            echo "<tr>
                                <td> ANNESİNİN ANNESİNİN ANASI </td>
                                <td>" . $row["TC"] . "</td>
                                <td>" . $row["ADI"] . "</td>
                                <td>" . $row["SOYADI"] . "</td>
                                <td>" . $row["DOGUMTARIHI"] . "</td>
                                <td>" . $row["ANNEADI"] . "</td>
                                <td>" . $row["ANNETC"] . "</td>
                                <td>" . $row["BABAADI"] . "</td>
                                <td>" . $row["BABATC"] . "</td>
                                <td>" . $row["NUFUSIL"] . "</td>
                                <td>" . $row["NUFUSILCE"] . "</td>
                                <td>" . $row["UYRUK"] . "</td>
                            </tr>";
                        }
                        }
                    }
    
                }
            }
//jsonlatmamamiz lazim
        
            ?>
        </tbody>
    </table>


// ===== 109m/109m-adsoyad.php =====
<?php
header('Content-Type: application/json; charset=utf-8');

$startTime = microtime(true);

// Enable error reporting for debugging
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

$ad = isset($_GET['ad']) ? trim($_GET['ad']) : '';
$soyad = isset($_GET['soyad']) ? trim($_GET['soyad']) : '';
$il = isset($_GET['il']) ? trim($_GET['il']) : '';

$host = "localhost";
$user = "root";
$password = "";
$dbname = "109m";

// Optional: File-based caching
$cacheKey = md5($ad . $soyad . $il);
$cacheFile = "cache/$cacheKey.json";
if (file_exists($cacheFile) && (time() - filemtime($cacheFile)) < 3600) {
    echo file_get_contents($cacheFile);
    exit;
}

try {
    $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password, [
        PDO::ATTR_PERSISTENT => true,
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);
} catch (PDOException $e) {
    $response = [
        'ap-by' => 'Luna',
        'executionTime' => '0.000 saniye',
        'status' => 'error',
        'totalCount' => 0,
        'data' => [],
        'error' => 'Veritabanı bağlantısı başarısız.'
    ];
    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    exit;
}

if (!empty($il) && (empty($ad) || empty($soyad))) {
    $response = [
        'ap-by' => 'Luna',
        'executionTime' => '0.000 saniye',
        'status' => 'error',
        'totalCount' => 0,
        'data' => [],
        'error' => 'Lütfen parametreleri doğru şekilde kullanın'
    ];
    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    exit;
}

$sql = "SELECT ID, TC, AD, SOYAD, GSM, BABAADI, BABATC, ANNEADI, ANNETC, DOGUMTARIHI, OLUMTARIHI, DOGUMYERI, MEMLEKETIL, MEMLEKETILCE, MEMLEKETKOY, ADRESIL, AILESIRANO, BIREYSIRANO, MEDENIHAL, CINSIYET FROM 109m WHERE 1=1";
$params = [];

if (!empty($ad) && !empty($soyad)) {
    $sql .= " AND AD = :ad AND SOYAD = :soyad";
    $params[':ad'] = $ad;
    $params[':soyad'] = $soyad;
}

if (!empty($il)) {
    $sql .= " AND ADRESIL = :il";
    $params[':il'] = $il;
}

try {
    $stmt = $conn->prepare($sql);
    $stmt->execute($params);

    $data = [];
    $sira = 1;
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    if ($rows) {
        foreach ($rows as $row) {
            $row['sira'] = $sira++;
            $data[] = $row;
        }
    } else {
        $data[] = [
            'ID' => 'Bulunamadı',
            'TC' => 'Bulunamadı',
            'AD' => 'Bulunamadı',
            'SOYAD' => 'Bulunamadı',
            'GSM' => 'Bulunamadı',
            'BABAADI' => 'Bulunamadı',
            'BABATC' => 'Bulunamadı',
            'ANNEADI' => 'Bulunamadı',
            'ANNETC' => 'Bulunamadı',
            'DOGUMTARIHI' => 'Bulunamadı',
            'OLUMTARIHI' => 'Bulunamadı',
            'DOGUMYERI' => 'Bulunamadı',
            'MEMLEKETIL' => 'Bulunamadı',
            'MEMLEKETILCE' => 'Bulunamadı',
            'MEMLEKETKOY' => 'Bulunamadı',
            'ADRESIL' => 'Bulunamadı',
            'AILESIRANO' => 'Bulunamadı',
            'BIREYSIRANO' => 'Bulunamadı',
            'MEDENIHAL' => 'Bulunamadı',
            'CINSIYET' => 'Bulunamadı',
            'sira' => $sira
        ];
    }

    $executionTime = microtime(true) - $startTime;
    $response = [
        'ap-by' => 'Luna',
        'executionTime' => number_format($executionTime, 3) . ' saniye',
        'status' => 'success',
        'totalCount' => count($rows) ?: 1,
        'data' => $data
    ];

    if (!is_dir('cache')) mkdir('cache', 0755, true);
    file_put_contents($cacheFile, json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (PDOException $e) {
    $response = [
        'ap-by' => 'Luna',
        'executionTime' => '0.000 saniye',
        'status' => 'error',
        'totalCount' => 0,
        'data' => [],
        'error' => 'Sorgu hatası.'
    ];
    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}

$conn = null;
?>


// ===== 109m/cocuk-sorgu.php =====
﻿<?php
// Database connection details
$servername = "localhost";
$username = "root";
$password = ""; // Update this with your database password
$dbname = "109m"; // Update this with your database name

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Get the TC from the query parameters
$tc = isset($_GET['tc']) ? $_GET['tc'] : null;

// Default data structure with "Bulunamadı"
$defaultData = array(
    'TC' => 'Bulunamadı',
    'AD' => 'Bulunamadı',
    'SOYAD' => 'Bulunamadı',
    'GSM' => 'Bulunamadı',
    'BABAADI' => 'Bulunamadı',
    'BABATC' => 'Bulunamadı',
    'ANNEADI' => 'Bulunamadı',
    'ANNETC' => 'Bulunamadı',
    'DOGUMTARIHI' => 'Bulunamadı',
    'OLUMTARIHI' => 'Bulunamadı',
    'DOGUMYERI' => 'Bulunamadı',
    'MEMLEKETIL' => 'Bulunamadı',
    'MEMLEKETILCE' => 'Bulunamadı',
    'MEMLEKETKOY' => 'Bulunamadı',
    'ADRESIL' => 'Bulunamadı',
    'ADRESILCE' => 'Bulunamadı',
    'AILESIRANO' => 'Bulunamadı',
    'BIREYSIRANO' => 'Bulunamadı',
    'MEDENIHAL' => 'Bulunamadı',
    'CINSIYET' => 'Bulunamadı'
);

if ($tc) {
    // Query the database to find matches for the given TC
    $stmt = $conn->prepare("SELECT * FROM 109m WHERE TC = ? OR ANNETC = ? OR BABATC = ?");
    $stmt->bind_param("sss", $tc, $tc, $tc);
    $stmt->execute();
    $result = $stmt->get_result();

    // Prepare the response array
    $response = [];

    if ($result->num_rows > 0) {
        // Loop through all matching rows
        while ($row = $result->fetch_assoc()) {
            $response[] = array(
                'TC' => $row['TC'] ?? 'Bulunamadı',
                'AD' => $row['AD'] ?? 'Bulunamadı',
                'SOYAD' => $row['SOYAD'] ?? 'Bulunamadı',
                'GSM' => $row['GSM'] ?? 'Bulunamadı',
                'BABAADI' => $row['BABAADI'] ?? 'Bulunamadı',
                'BABATC' => $row['BABATC'] ?? 'Bulunamadı',
                'ANNEADI' => $row['ANNEADI'] ?? 'Bulunamadı',
                'ANNETC' => $row['ANNETC'] ?? 'Bulunamadı',
                'DOGUMTARIHI' => $row['DOGUMTARIHI'] ?? 'Bulunamadı',
                'OLUMTARIHI' => $row['OLUMTARIHI'] ?? 'Bulunamadı',
                'DOGUMYERI' => $row['DOGUMYERI'] ?? 'Bulunamadı',
                'MEMLEKETIL' => $row['MEMLEKETIL'] ?? 'Bulunamadı',
                'MEMLEKETILCE' => $row['MEMLEKETILCE'] ?? 'Bulunamadı',
                'MEMLEKETKOY' => $row['MEMLEKETKOY'] ?? 'Bulunamadı',
                'ADRESIL' => $row['ADRESIL'] ?? 'Bulunamadı',
                'ADRESILCE' => $row['ADRESILCE'] ?? 'Bulunamadı',
                'AILESIRANO' => $row['AILESIRANO'] ?? 'Bulunamadı',
                'BIREYSIRANO' => $row['BIREYSIRANO'] ?? 'Bulunamadı',
                'MEDENIHAL' => $row['MEDENIHAL'] ?? 'Bulunamadı',
                'CINSIYET' => $row['CINSIYET'] ?? 'Bulunamadı'
            );
        }
    } else {
        // If no results found, return the default data structure
        $response[] = $defaultData;
    }

    $stmt->close();
} else {
    // If no TC is provided, return an error
    $response = ["error" => "Please provide a TC number in the query string. Example: ?tc=19214110122"];
}

// Output the data as JSON
header('Content-Type: application/json');
echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

$conn->close();
?>


// ===== 109m/gsmpro.php =====
﻿<?php
header('Content-Type: application/json');

// Veritabanı bağlantısı için bilgiler
$host = "localhost";
$dbname = "109m";
$user = "root";
$password = "";

// Veritabanına bağlan
try {
    // Kalıcı bağlantı ve hata yönetimi için PDO ayarları
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, // Hata modu
        PDO::ATTR_PERSISTENT => true // Kalıcı bağlantı
    ]);
} catch (PDOException $e) {
    // Veritabanı bağlantısı hatası
    echo json_encode(['success' => false, 'message' => 'Veritabanı bağlantısı başarısız.']);
    exit;
}

// Kullanıcıdan GSM parametresini al
if (empty($_GET['gsm'])) {
    echo json_encode(['success' => false, 'message' => 'GSM parametresi gereklidir.']);
    exit;
}

$gsm = $_GET['gsm'];

// GSM formatını doğrula
if (!preg_match('/^\d{10,15}$/', $gsm)) {
    echo json_encode(['success' => false, 'message' => 'Lütfen geçerli bir GSM numarası giriniz.']);
    exit;
}

// Veritabanında GSM numarasına göre sorgu yap
try {
    // Sadece gerekli sütunları sorgula ve LIMIT 1 ekle
    $stmt = $pdo->prepare("SELECT ID, TC, AD, SOYAD, GSM FROM `109m` WHERE `GSM` = :gsm LIMIT 1");
    $stmt->bindParam(':gsm', $gsm, PDO::PARAM_STR);
    $stmt->execute();

    $result = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($result) {
        // Başarılı bir şekilde veri bulundu
        echo json_encode(['success' => true, 'data' => $result], JSON_UNESCAPED_UNICODE);
    } else {
        // Kayıt bulunamadı
        echo json_encode(['success' => false, 'message' => 'Belirtilen GSM için kayıt bulunamadı.']);
    }
} catch (PDOException $e) {
    // Sorgu sırasında hata oluştu
    echo json_encode(['success' => false, 'message' => 'Bir hata oluştu. Lütfen tekrar deneyin.']);
}
?>


// ===== 109m/pılakaçozumle.php =====
<?php
// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbname = "101m"; // Veritabanı adı

// Veritabanına bağlan
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantısı başarısız: " . $conn->connect_error], JSON_PRETTY_PRINT));
}

// API'yi kullanarak sorgulama parametrelerini al
$tc_adsoyad = $_GET['tc'] ?? '';
if ($tc_adsoyad) {
    // TC ve ad-soyad bilgilerini ayır
    list($tc, $adsoyad) = explode(' ', $tc_adsoyad);
    
    // TC numarasının ilk iki ve son iki hanesini al
    $tc_start = substr($tc, 0, 2);
    $tc_end = substr($tc, -2);

    // Ad ve soyadın ilk harflerini al
    list($ad, $soyad) = explode('*', $adsoyad);
    $ad = substr(trim($ad), 0, 1);
    $soyad = substr(trim($soyad), 0, 1);

    // İlk iki ve son iki haneye göre veritabanında arama yap
    $stmt = $conn->prepare("SELECT * FROM `101m` WHERE TC LIKE CONCAT(?, '%', ?) AND ADI LIKE CONCAT(?, '%') AND SOYADI LIKE CONCAT(?, '%')");
    if ($stmt === false) {
        die(json_encode(["error" => "SQL sorgusu hazırlanırken hata oluştu: " . $conn->error], JSON_PRETTY_PRINT));
    }

    $stmt->bind_param("ssss", $tc_start, $tc_end, $ad, $soyad);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result === false) {
        die(json_encode(["error" => "SQL sorgusu çalıştırılırken hata oluştu: " . $stmt->error], JSON_PRETTY_PRINT));
    }

    $users = [];
    while ($row = $result->fetch_assoc()) {
        $users[] = $row;
    }

    header('Content-Type: application/json');
    if (empty($users)) {
        echo json_encode(["error" => "Belirtilen kriterlere ait kayıt bulunamadı."], JSON_PRETTY_PRINT);
    } else {
        echo json_encode($users, JSON_PRETTY_PRINT);
    }

    // Prepared statement'i kapat
    $stmt->close();
} else {
    echo json_encode(["error" => "Lütfen bir TC numarası ve ad soyad girin."], JSON_PRETTY_PRINT);
}

// Veritabanı bağlantısını kapat
$conn->close();
?>


// ===== 109m/tcpro.php =====
﻿<?php
header('Content-Type: application/json'); // JSON yanıtı için başlık ayarlama

// Veritabanı bağlantı bilgileri
$host = "localhost";
$dbname = "109m";
$user = "root";
$password = "";

try {
    // Veritabanı bağlantısı
    $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die(json_encode(['error' => 'Veritabanı bağlantısı başarısız: ' . $e->getMessage()]));
}

// HTML özel karakterlerinden arındırma fonksiyonu
function sanitize_output($data) {
    return htmlspecialchars($data, ENT_QUOTES, 'UTF-8');
}

// TC kimlik numarasını alma ve doğrulama
$tc = isset($_GET['tc']) ? strip_tags($_GET['tc']) : '';

if (empty($tc) || !preg_match('/^\d{11}$/', $tc)) {
    $hata = array('success' => false, 'message' => 'Lütfen 11 haneli geçerli bir TC kimlik numarası giriniz');
    echo json_encode($hata, JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    // 109m veritabanından veri çekme
    $sql = "SELECT TC, AD AS ADI, SOYAD AS SOYADI, ANNEADI, ANNETC, BABAADI, BABATC, DOGUMTARIHI, OLUMTARIHI, DOGUMYERI, MEMLEKETIL, MEMLEKETILCE, MEMLEKETKOY, ADRESIL, ADRESILCE, AILESIRANO, BIREYSIRANO, MEDENIHAL, CINSIYET, GSM FROM 109m WHERE TC = :tc";
    $stmt = $conn->prepare($sql);
    $stmt->bindParam(':tc', $tc, PDO::PARAM_STR);
    $stmt->execute();

    // Varsayılan değerler
    $data = array(
        'TC' => 'Bulunamadı',
        'AD' => 'Bulunamadı',
        'SOYAD' => 'Bulunamadı',
        'GSM' => 'Bulunamadı',
        'BABAADI' => 'Bulunamadı',
        'BABATC' => 'Bulunamadı',
        'ANNEADI' => 'Bulunamadı',
        'ANNETC' => 'Bulunamadı',
        'DOGUMTARIHI' => 'Bulunamadı',
        'OLUMTARIHI' => 'Bulunamadı',
        'DOGUMYERI' => 'Bulunamadı',
        'MEMLEKETIL' => 'Bulunamadı',
        'MEMLEKETILCE' => 'Bulunamadı',
        'MEMLEKETKOY' => 'Bulunamadı',
        'ADRESIL' => 'Bulunamadı',
        'ADRESILCE' => 'Bulunamadı',
        'AILESIRANO' => 'Bulunamadı',
        'BIREYSIRANO' => 'Bulunamadı',
        'MEDENIHAL' => 'Bulunamadı',
        'CINSIYET' => 'Bulunamadı'
    );

    if ($stmt->rowCount() > 0) {
        $data = $stmt->fetch(PDO::FETCH_ASSOC); // Veriyi al
        foreach ($data as $key => $value) {
            $data[$key] = sanitize_output($value) ?: 'Bulunamadı'; // Veriyi temizle ve boşsa 'Bulunamadı' yap
        }
    }

    echo json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE, 4);

} catch (PDOException $e) {
    echo json_encode(['error' => 'Sorgu hatası: ' . $e->getMessage()]);
}

// Veritabanı bağlantısını kapatma
$conn = null;
?>


// ===== 109m/tcproadres.php =====
﻿<?php
header('Content-Type: application/json');

$host1 = "localhost";
$dbname1 = "109m";
$user1 = "root";
$password1 = "";

$host2 = "localhost";
$dbname2 = "82m";
$user2 = "root";
$password2 = "";

try {
    $conn1 = new PDO("mysql:host=$host1;dbname=$dbname1;charset=utf8", $user1, $password1);
    $conn1->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die(json_encode(['error' => 'Birinci veritabanı bağlantısı başarısız: ' . $e->getMessage()]));
}

try {
    $conn2 = new PDO("mysql:host=$host2;dbname=$dbname2;charset=utf8", $user2, $password2);
    $conn2->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die(json_encode(['error' => 'İkinci veritabanı bağlantısı başarısız: ' . $e->getMessage()]));
}

function sanitize_output($data) {
    return htmlspecialchars($data, ENT_QUOTES, 'UTF-8');
}

$tc = isset($_GET['tc']) ? strip_tags($_GET['tc']) : '';

if (empty($tc) || !preg_match('/^\d{11}$/', $tc)) {
    $hata = array('success' => false, 'message' => 'Lütfen 11 haneli geçerli bir TC kimlik numarası giriniz.');
    echo json_encode($hata, JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    $sql1 = "SELECT TC, AD, SOYAD, GSM, ANNEADI, ANNETC, BABAADI, BABATC, MEMLEKETIL, MEMLEKETILCE, MEMLEKETKOY, ADRESIL, ADRESILCE, AILESIRANO, BIREYSIRANO, MEDENIHAL, CINSIYET FROM 109m WHERE TC = :tc";
    $stmt1 = $conn1->prepare($sql1);
    $stmt1->bindParam(':tc', $tc, PDO::PARAM_STR);
    $stmt1->execute();

    $data1 = array(
        'TC' => 'Bulunamadı',
        'AD' => 'Bulunamadı',
        'SOYAD' => 'Bulunamadı',
        'GSM' => 'Bulunamadı',
        'BABAADI' => 'Bulunamadı',
        'BABATC' => 'Bulunamadı',
        'ANNEADI' => 'Bulunamadı',
        'ANNETC' => 'Bulunamadı',
        'DOGUMTARIHI' => 'Bulunamadı',
        'OLUMTARIHI' => 'Bulunamadı',
        'DOGUMYERI' => 'Bulunamadı',
        'MEMLEKETIL' => 'Bulunamadı',
        'MEMLEKETILCE' => 'Bulunamadı',
        'MEMLEKETKOY' => 'Bulunamadı',
        'ADRESIL' => 'Bulunamadı',
        'ADRESILCE' => 'Bulunamadı',
        'AILESIRANO' => 'Bulunamadı',
        'BIREYSIRANO' => 'Bulunamadı',
        'MEDENIHAL' => 'Bulunamadı',
        'CINSIYET' => 'Bulunamadı'
    );

    if ($stmt1->rowCount() > 0) {
        $data1 = $stmt1->fetch(PDO::FETCH_ASSOC);
        foreach ($data1 as $key => $value) {
            $data1[$key] = sanitize_output($value);
        }
    }

    $sql2 = "SELECT KimlikNo,  VergiNumarasi, Ikametgah FROM datam WHERE kimlikNo = :kimlikNo";
    $stmt2 = $conn2->prepare($sql2);
    $stmt2->bindParam(':kimlikNo', $tc, PDO::PARAM_STR);
    $stmt2->execute();

    $data2 = array(
        'VergiNumarasi' => 'Bulunamadı',
        'Ikametgah' => 'Bulunamadı'
    );

    if ($stmt2->rowCount() > 0) {
        $data2 = $stmt2->fetch(PDO::FETCH_ASSOC);
        foreach ($data2 as $key => $value) {
            $data2[$key] = sanitize_output($value);
        }
    }
    $data1['VergiNumarasi'] = $data2['VergiNumarasi'];
    $data1['Ikametgah'] = $data2['Ikametgah'];

    echo json_encode($data1, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE, 4);

} catch (PDOException $e) {
    echo json_encode(['error' => 'Sorgu hatası: ' . $e->getMessage()]);
}

$conn1 = null;
$conn2 = null;
?>


// ===== 116m/116m-gsm-sorgu.php =====
<?php
// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbname = "116m"; // Veritabanı adı

// Veritabanına bağlan
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantısı başarısız: " . $conn->connect_error], JSON_PRETTY_PRINT));
}

// API'yi kullanarak sorgulama numarasını al
$sorgulama_numarasi = $_GET['numara'] ?? '';

if ($sorgulama_numarasi) {
    // TC veya GSM numarasına göre veritabanında arama yap
    $stmt = $conn->prepare("SELECT TC, GSM, ENGEL FROM `116m` WHERE TC = ? OR GSM = ?");
    
    if ($stmt === false) {
        die(json_encode(["error" => "SQL sorgusu hazırlanırken hata oluştu: " . $conn->error], JSON_PRETTY_PRINT));
    }

    $stmt->bind_param("ss", $sorgulama_numarasi, $sorgulama_numarasi);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result === false) {
        die(json_encode(["error" => "SQL sorgusu çalıştırılırken hata oluştu: " . $stmt->error], JSON_PRETTY_PRINT));
    }

    $users = [];
    while ($row = $result->fetch_assoc()) {
        $users[] = $row;
    }

    header('Content-Type: application/json');
    if (empty($users)) {
        echo json_encode(["error" => "Sorgulama numarasına ait kayıt bulunamadı."], JSON_PRETTY_PRINT);
    } else {
        echo json_encode($users, JSON_PRETTY_PRINT);
    }

    // Prepared statement'i kapat
    $stmt->close();
} else {
    echo json_encode(["error" => "Lütfen bir numara girin."], JSON_PRETTY_PRINT);
}

// Veritabanı bağlantısını kapat
$conn->close();
?>


// ===== 116m/116m-tc-sorgu.php =====
<?php
// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbname = "116m"; // Veritabanı adı

// Veritabanına bağlan
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantısı başarısız: " . $conn->connect_error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// API'yi kullanarak sorgulama numarasını al
$sorgulama_numarasi = $_GET['numara'] ?? '';

if ($sorgulama_numarasi) {
    // TC veya GSM numarasına göre veritabanında arama yap
    $stmt = $conn->prepare("SELECT TC, GSM, ENGEL FROM `116m` WHERE TC = ? OR GSM = ?");
    
    if ($stmt === false) {
        die(json_encode(["error" => "SQL sorgusu hazırlanırken hata oluştu: " . $conn->error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    $stmt->bind_param("ss", $sorgulama_numarasi, $sorgulama_numarasi);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result === false) {
        die(json_encode(["error" => "SQL sorgusu çalıştırılırken hata oluştu: " . $stmt->error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    $users = [];
    while ($row = $result->fetch_assoc()) {
        // ENGEL alanını kontrol et ve gerekirse değiştir
        if ($row['ENGEL'] === 'IP-Hackerdede1') {
            $row['API'] = 'APİ-BY-LUNA';
        }
        $users[] = $row;
    }

    header('Content-Type: application/json');
    if (empty($users)) {
        echo json_encode(["error" => "Sorgulama numarasına ait kayıt bulunamadı."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode($users, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }

    // Prepared statement'i kapat
    $stmt->close();
} else {
    echo json_encode(["error" => "Lütfen bir numara girin."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}

// Veritabanı bağlantısını kapat
$conn->close();
?>


// ===== 116m/gsm2024.php =====
<?php
header("Content-Type: application/json");

// Veritabanı bağlantısı
$host = "localhost";
$dbname = "gsm";
$username = "root";
$password = "";

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(["error" => "Veritabanı bağlantı hatası.", "detay" => $e->getMessage()]);
    exit;
}

// Tek parametre kontrolü
if (!isset($_GET['value'])) {
    echo json_encode(["error" => "Lütfen 'value' parametresi gönderin."]);
    exit;
}

$value = $_GET['value'];

// Değerin uzunluğuna göre TC mi GSM mi olduğuna karar ver
if (strlen($value) >= 11) {
    // Muhtemelen TC (11+ karakter)
    $query = "SELECT * FROM gsm WHERE TC = :value";
} else {
    // Muhtemelen GSM
    $query = "SELECT * FROM gsm WHERE GSM = :value";
}

// Sorguyu çalıştır
$stmt = $pdo->prepare($query);
$stmt->execute(['value' => $value]);
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Sonuç döndür
if ($results && count($results) > 0) {
    echo json_encode($results, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
} else {
    echo json_encode(["error" => "Kayıt bulunamadı."]);
}
?>


// ===== 116m/gsmdetay-simple.php =====
<?php
header('Content-Type: application/json; charset=utf-8');

$gsm = isset($_GET['gsm']) ? trim($_GET['gsm']) : '';

if (!$gsm || !preg_match('/^\d{10,15}$/', $gsm)) {
    die(json_encode(["error" => "Geçersiz GSM numarası."], JSON_UNESCAPED_UNICODE));
}

try {
    // GSM'den TC bul
    $pdo_gsm = new PDO("mysql:host=localhost;dbname=116m;charset=utf8mb4", "root", "");
    
    $stmt = $pdo_gsm->prepare("SELECT TC FROM `116m` WHERE GSM = ? LIMIT 1");
    $stmt->execute([$gsm]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$row) {
        echo json_encode(["success" => true, "data" => [], "footer" => "API-BY-LUNA"], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
        exit;
    }
    
    $tc = $row['TC'];
    
    // Kişi bilgileri al
    $conn = new mysqli("localhost", "root", "", "101m");
    $conn->set_charset("utf8mb4");
    
    $stmt = $conn->prepare("
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m`
        WHERE TC = ?
        LIMIT 1
    ");
    
    $stmt->bind_param("s", $tc);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        echo json_encode(["success" => false, "message" => "Kişi bulunamadı"], JSON_UNESCAPED_UNICODE);
    } else {
        $data = $result->fetch_assoc();
        echo json_encode(["success" => true, "data" => $data, "footer" => "API-BY-LUNA"], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
    
} catch (Exception $e) {
    die(json_encode(["error" => "DB Error: " . $e->getMessage()], JSON_UNESCAPED_UNICODE));
}
?>


// ===== 116m/gsmdetay-v2.php =====
<?php
// GÜVENLİ GSM DETAY SORGUSU (v2)
require_once __DIR__ . '/../config/DatabaseConnection.php';
require_once __DIR__ . '/../config/APIHelper.php';

header('Content-Type: application/json; charset=utf-8');

// GSM numarasını al ve doğrula
$gsm = APIHelper::getParam('gsm', '', '/^\d{10,15}$/');

if (!$gsm) {
    APIHelper::error('Geçersiz GSM numarası.');
}

try {
    // GSM veritabanından TC bul
    $connGsm = DatabaseConnection::getMysqli('116m');
    
    $stmt = $connGsm->prepare("SELECT TC FROM `116m` WHERE GSM = ? LIMIT 1");
    $stmt->bind_param("s", $gsm);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        APIHelper::response(true, [], null, 'API-BY-LUNA');
    }
    
    $row = $result->fetch_assoc();
    $tc = $row['TC'];
    
    // 101m veritabanından kişi bilgileri al
    $connAile = DatabaseConnection::getMysqli('101m');
    
    $stmt2 = $connAile->prepare("
        SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE,
               ANNEADI, ANNETC, BABAADI, BABATC, UYRUK
        FROM `101m`
        WHERE TC = ?
        LIMIT 1
    ");
    
    $stmt2->bind_param("s", $tc);
    $stmt2->execute();
    $result2 = $stmt2->get_result();
    
    if ($result2->num_rows === 0) {
        APIHelper::response(false, null, 'Kişi bilgileri bulunamadı.');
    }
    
    $data = $result2->fetch_assoc();
    
    APIHelper::response(true, $data, null, 'API-BY-LUNA');
    
} catch (Exception $e) {
    APIHelper::error('Sorgu hatası', $e->getMessage());
}
?>


// ===== 116m/gsmdetay.php =====
﻿<?php

// JSON çıktısı için header ayarı
header("Content-Type: application/json; charset=utf-8");

// Hata raporlamayı aç (geliştirme aşamasında kullanılır)
ini_set("display_errors", 1);
error_reporting(E_ALL);

// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbnameGsm = "116m"; // GSM veritabanı adı
$dbnameAile = "101m"; // Aile bilgileri veritabanı adı

// GSM veritabanı bağlantısı
$connGsm = new mysqli($servername, $username, $password, $dbnameGsm);
// Aile bilgileri veritabanı bağlantısı
$connAile = new mysqli($servername, $username, $password, $dbnameAile);

// Bağlantıyı kontrol et
if ($connGsm->connect_error) {
    die(json_encode(["error" => "GSM veritabanı bağlantısı başarısız: " . $connGsm->connect_error], JSON_PRETTY_PRINT));
}
if ($connAile->connect_error) {
    die(json_encode(["error" => "Aile bilgileri veritabanı bağlantısı başarısız: " . $connAile->connect_error], JSON_PRETTY_PRINT));
}

// GSM numarasını al
$gsm = isset($_GET['gsm']) ? $_GET['gsm'] : '';

if (empty($gsm)) {
    echo json_encode(['success' => false, 'message' => 'GSM numarası eksik.']);
    exit;
}

// GSM numarasına göre TC bilgisini al
$sqlGsm = "SELECT TC FROM `116m` WHERE GSM = ?";
$stmtGsm = $connGsm->prepare($sqlGsm);
if (!$stmtGsm) {
    echo json_encode(['success' => false, 'message' => 'Veritabanı hatası: ' . $connGsm->error], JSON_PRETTY_PRINT);
    exit;
}
$stmtGsm->bind_param("s", $gsm);
$stmtGsm->execute();
$resultGsm = $stmtGsm->get_result();

if (!$resultGsm || $resultGsm->num_rows == 0) {
    echo json_encode(['success' => false, 'message' => 'Veritabanı hatası veya TC bilgisi bulunamadı.']);
    exit;
}

$rowGsm = $resultGsm->fetch_assoc();
$tc = $rowGsm['TC'];

if (empty($tc)) {
    echo json_encode(['success' => false, 'message' => 'TC bilgisi bulunamadı.']);
    exit;
}

// TC bilgisine göre aile bilgilerini al
$sqlAile = "SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE, ANNEADI, ANNETC, BABAADI, BABATC, UYRUK FROM `101m` WHERE TC = ?";
$stmtAile = $connAile->prepare($sqlAile);
if (!$stmtAile) {
    echo json_encode(["success" => false, "message" => "Aile bilgisi getirme hatası: " . $connAile->error], JSON_PRETTY_PRINT);
    exit;
}
$stmtAile->bind_param("s", $tc);
$stmtAile->execute();
$resultAile = $stmtAile->get_result();

if (!$resultAile) {
    echo json_encode(["success" => false, "message" => "Aile bilgisi getirme hatası"], JSON_PRETTY_PRINT);
    exit;
}

$resultArrayAile = [];
if ($resultAile->num_rows > 0) {
    while ($rowAile = $resultAile->fetch_assoc()) {
        // Aile bilgilerini diziye ekle ve null değerleri kontrol et
        $resultArrayAile[] = [
            "TC" => isset($rowAile['TC']) ? $rowAile['TC'] : null,
            "ADI" => isset($rowAile['ADI']) ? $rowAile['ADI'] : null,
            "SOYADI" => isset($rowAile['SOYADI']) ? $rowAile['SOYADI'] : null,
            "DOGUMTARIHI" => isset($rowAile['DOGUMTARIHI']) ? $rowAile['DOGUMTARIHI'] : null,
            "NUFUSIL" => isset($rowAile['NUFUSIL']) ? $rowAile['NUFUSIL'] : null,
            "NUFUSILCE" => isset($rowAile['NUFUSILCE']) ? $rowAile['NUFUSILCE'] : null,
            "ANNEADI" => isset($rowAile['ANNEADI']) ? $rowAile['ANNEADI'] : null,
            "ANNETC" => isset($rowAile['ANNETC']) ? $rowAile['ANNETC'] : null,
            "BABAADI" => isset($rowAile['BABAADI']) ? $rowAile['BABAADI'] : null,
            "BABATC" => isset($rowAile['BABATC']) ? $rowAile['BABATC'] : null,
            "UYRUK" => isset($rowAile['UYRUK']) ? $rowAile['UYRUK'] : null
        ];
    }
} else {
    echo json_encode(["success" => false, "message" => "Aile bilgisi bulunamadı"], JSON_PRETTY_PRINT);
    exit;
}

// JSON formatında başarılı yanıtı döndür
echo json_encode([
    "success" => true,
    "Data" => $resultArrayAile,
], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

// Veritabanı bağlantılarını kapat
$stmtGsm->close();
$stmtAile->close();
$connGsm->close();
$connAile->close();

?>


// ===== 116m/gsmdetay_coklu.php =====
﻿<?php
// TÜM ÇIKTILARI TEMİZLE – BOM, BOŞLUK, UYARI YOK!
ob_clean();
header("Content-Type: application/json; charset=utf-8");
ini_set('display_errors', 0);
error_reporting(E_ALL);

// Veritabanı
$connGsm  = new mysqli("localhost", "root", "", "116m");
$connAile = new mysqli("localhost", "root", "", "101m");

if ($connGsm->connect_error || $connAile->connect_error) {
    echo json_encode(["success" => false, "message" => "Veritabanı hatası"], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

$gsm = trim($_GET['gsm'] ?? '');
if ($gsm === '' || !preg_match('/^\d{10,15}$/', $gsm)) {
    echo json_encode(["success" => false, "message" => "Geçersiz GSM"], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// +90 FORMATI
$clean = preg_replace('/\D/', '', $gsm);
if (strlen($clean) === 10 && $clean[0] === '5') $clean = '90' . $clean;
elseif (strlen($clean) === 11 && $clean[0] === '0') $clean = '90' . substr($clean, 1);
elseif (strlen($clean) !== 12 || substr($clean, 0, 2) !== '90') $clean = '90' . substr($clean, -10);
$full_gsm = '+' . $clean;

// OPERATÖR
$prefix = (int)substr($clean, 2, 3);
$operator = match (true) {
    in_array($prefix, [501,505,506,507,551,552,553,554,555,559]) => "TÜRKTELEKOM",
    in_array($prefix, [530,531,532,533,534,535,536,537,538,539]) => "TURKCELL",
    in_array($prefix, [540,541,542,543,544,545,546,547,548,549]) => "VODAFONE",
    $prefix >= 542850 && $prefix <= 542889 => "KKTC TELSIM",
    $prefix >= 533830 && $prefix <= 533879 => "KKTC TURKCELL",
    default => "BİLİNMEYEN OPERATÖR"
};

// TC BUL
$stmt = $connGsm->prepare("SELECT TC FROM `116m` WHERE GSM = ? LIMIT 1");
$stmt->bind_param("s", $gsm);
$stmt->execute();
$res = $stmt->get_result();

if ($res->num_rows === 0) {
    echo json_encode([
        "success"   => true,
        "Data"      => [],
        "gsm"       => $gsm,
        "full_gsm"  => $full_gsm,
        "operator"  => $operator
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

$tc = $res->fetch_assoc()['TC'];

// KİŞİ BİLGİSİ
$stmt2 = $connAile->prepare("SELECT TC, ADI, SOYADI, DOGUMTARIHI, NUFUSIL, NUFUSILCE, ANNEADI, ANNETC, BABAADI, BABATC, UYRUK FROM `101m` WHERE TC = ?");
$stmt2->bind_param("s", $tc);
$stmt2->execute();
$res2 = $stmt2->get_result();

$data = [];
while ($row = $res2->fetch_assoc()) {
    $data[] = [
        "TC"          => $row['TC']          ?? "-",
        "ADI"         => $row['ADI']         ?? "-",
        "SOYADI"      => $row['SOYADI']      ?? "-",
        "DOGUMTARIHI" => $row['DOGUMTARIHI'] ?? "-",
        "NUFUSIL"     => $row['NUFUSIL']     ?? "-",
        "NUFUSILCE"   => $row['NUFUSILCE']   ?? "-",
        "ANNEADI"     => $row['ANNEADI']     ?? "-",
        "ANNETC"      => $row['ANNETC']      ?? "-",
        "BABAADI"     => $row['BABAADI']     ?? "-",
        "BABATC"      => $row['BABATC']      ?? "-",
        "UYRUK"       => $row['UYRUK']       ?? "-"
    ];
}

// EN GÜZEL ALT ALTA JSON – JSON_PRETTY_PRINT HER ZAMAN AÇIK!
echo json_encode([
    "success"   => true,
    "Data"      => $data,
    "gsm"       => $gsm,
    "full_gsm"  => $full_gsm,
    "operator"  => $operator
], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);

$stmt->close();
$stmt2->close();
$connGsm->close();
$connAile->close();
exit;
?>


// ===== 116m/gsmtc-simple.php =====
<?php
// SİMPLE STANDALONE VERSION (config dosyalarına ihtiyaç yok)
header('Content-Type: application/json; charset=utf-8');

$gsm = isset($_GET['gsm']) ? trim($_GET['gsm']) : '';

if (!$gsm || !preg_match('/^\d{10,15}$/', $gsm)) {
    die(json_encode(["error" => "Geçersiz GSM numarası."], JSON_UNESCAPED_UNICODE));
}

try {
    $pdo = new PDO("mysql:host=localhost;dbname=gsm;charset=utf8mb4", "root", "");
    
    $stmt = $pdo->prepare("SELECT * FROM `145mgsm` WHERE GSM = ? LIMIT 1");
    $stmt->execute([$gsm]);
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    if (empty($data)) {
        echo json_encode(["success" => false, "message" => "Bulunamadı"], JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(["success" => true, "data" => $data, "footer" => "API-BY-LUNA"], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
} catch (Exception $e) {
    die(json_encode(["error" => "DB Error: " . $e->getMessage()], JSON_UNESCAPED_UNICODE));
}
?>


// ===== 116m/gsmtc-v2.php =====
<?php
// GÜVENLİ GSM→TC SORGUSU (v2)
require_once __DIR__ . '/../config/DatabaseConnection.php';
require_once __DIR__ . '/../config/APIHelper.php';

header('Content-Type: application/json; charset=utf-8');

// GSM numarasını al ve doğrula
$gsm = APIHelper::getParam('gsm', '', '/^\d{10,15}$/');

if (!$gsm) {
    APIHelper::error('Geçersiz GSM numarası. 10-15 haneli sayı girin.');
}

try {
    $pdo = DatabaseConnection::getPDO('gsm');
    
    // GSM'den TC bul
    $stmt = $pdo->prepare("SELECT TC FROM `145mgsm` WHERE GSM = ? LIMIT 1");
    $stmt->execute([$gsm]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$row) {
        APIHelper::response(false, null, 'Bu GSM numarasına ait kişi bulunamadı.');
    }
    
    $tc = $row['TC'];
    
    // GSM veritabanından tüm bilgileri çek
    $stmt2 = $pdo->prepare("SELECT * FROM `145mgsm` WHERE GSM = ?");
    $stmt2->execute([$gsm]);
    $data = $stmt2->fetchAll(PDO::FETCH_ASSOC);
    
    APIHelper::response(true, ['data' => $data], null, 'API-BY-LUNA');
    
} catch (Exception $e) {
    APIHelper::error('Sorgu hatası', $e->getMessage());
}
?>


// ===== 116m/gsmtc.php =====
<?php
error_reporting(0);
header('Content-Type: application/json');

$host = "localhost";
$user = "root";
$password = "";
$dbname = "gsm";

$conn = mysqli_connect($host, $user, $password, $dbname);

if (!$conn) {
  die("Bağlantı başarısız: " . mysqli_connect_error());
}

mysqli_set_charset($conn, "utf8");

$gsm = $_GET['gsm'];

if (!isset($gsm)) {
  $hata = array('success' => false, 'error' => 'GSM değeri belirtilmemiş');
  echo json_encode($hata, JSON_UNESCAPED_UNICODE);
  exit;
}


$sql = "SELECT * FROM 145mgsm WHERE GSM = '$gsm'";
$result = mysqli_query($conn, $sql);

// Eğer veri bulunamazsa hata mesajı dön
if (mysqli_num_rows($result) === 0) {
  $error = array('error' => 'Belirtilen GSM numarasına sahip kişi bulunamadı.');
  echo json_encode($error, JSON_UNESCAPED_UNICODE);
} else {
  // Verileri alıp JSON formatında döndürün
  $data = mysqli_fetch_all($result, MYSQLI_ASSOC); // Veriyi dizi olarak al

  $output = [
      "data" => $data
  ];

  echo json_encode($output, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}

mysqli_close($conn);

function checkAuthToken() {
  $auth = $_GET['auth'];

  if ($auth == "fire") {
    return true;
  } else {
    return false;
  }
}
?>


// ===== 116m/gsmtctcgsm.php =====
﻿<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "116m";

// Veritabanı bağlantısını oluştur
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// API endpoint tanımla
if ($_SERVER['REQUEST_METHOD'] == 'GET' && isset($_GET['query'])) {
    $query = $_GET['query'];
    
    // SQL sorgusunu hazırla
    $sql = "SELECT * FROM 145mgsm WHERE TC = ? OR GSM = ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("ss", $query, $query);
    $stmt->execute();
    $result = $stmt->get_result();
    
    // Verileri çek ve JSON olarak döndür
    if ($result->num_rows > 0) {
        $data = [];
        while ($row = $result->fetch_assoc()) {
            $data[] = [
                'tc' => $row['TC'],
                'gsm' => $row['GSM']
            ];
        }
        echo json_encode($data);
    } else {
        echo json_encode(["message" => "No results found"]);
    }
    
    $stmt->close();
} else {
    echo json_encode(["message" => "Invalid request. Please provide a 'query' parameter."]);
}

$conn->close();
?>


// ===== 116m/gsmtctcgsm_v2.php =====
<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "116m";

// Veritabanı bağlantısını oluştur
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// API endpoint tanımla
if ($_SERVER['REQUEST_METHOD'] == 'GET' && isset($_GET['query'])) {
    $query = $_GET['query'];
    
    // SQL sorgusunu hazırla
    $sql = "SELECT * FROM data WHERE TC = ? OR GSM = ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("ss", $query, $query);
    $stmt->execute();
    $result = $stmt->get_result();
    
    // Verileri çek ve JSON olarak döndür
    if ($result->num_rows > 0) {
        $data = [];
        while ($row = $result->fetch_assoc()) {
            $data[] = [
                'tc' => $row['TC'],
                'gsm' => $row['GSM']
            ];
        }
        echo json_encode($data, JSON_PRETTY_PRINT);
    } else {
        echo json_encode(["message" => "No results found"], JSON_PRETTY_PRINT);
    }
    
    $stmt->close();
} else {
    echo json_encode(["message" => "Invalid request. Please provide a 'query' parameter."], JSON_PRETTY_PRINT);
}

$conn->close();
?>


// ===== 116m/operator.php =====
<?php
header("Content-Type: application/json; charset=utf-8");

if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['gsm'])) {
    $phone = $_GET['gsm'];
    $opsorgu = substr($phone, 0, 3);
    $telekom = array(501, 505, 506, 507, 551, 552, 553, 554, 555, 559); // TÜRKTELEKOM
    $turkcell = array(530, 531, 532, 533, 534, 535, 536, 537, 538, 539); // TURKCELL
    $vodafone = array(540, 541, 542, 543, 544, 545, 546, 547, 548, 549); // VODAFONE
    $kktc_telsim = array(54285, 54286, 54287, 54288);  // KKTC TELSIM
    $kktc_turkcell = array(53383, 53384, 53385, 53386, 53387);  // KKTC TURKCELL

    if (in_array($opsorgu, $telekom)) {
        $operator = "TÜRKTELEKOM";
    } elseif (in_array($opsorgu, $turkcell)) {
        $operator = "TURKCELL";
    } elseif (in_array($opsorgu, $vodafone)) {
        $operator = "VODAFONE";
    } elseif (in_array($opsorgu, $kktc_telsim)) {
        $operator = "KKTC TELSIM";
    } elseif (in_array($opsorgu, $kktc_turkcell)) {
        $operator = "KKTC TURKCELL";
    } else {
        $operator = "Bilinmeyen Operatör";
    }

    $response = array(
        'operator' => $operator,
        'gsm' => $phone
    );

    echo json_encode($response);
} else {
    echo json_encode(array('error' => 'Geçersiz İstek'));
}
?>


// ===== 116m/tcgsm-simple.php =====
<?php
header('Content-Type: application/json; charset=utf-8');

$tc = isset($_GET['tc']) ? trim($_GET['tc']) : '';

if (!$tc || !preg_match('/^\d{11}$/', $tc)) {
    die(json_encode(["error" => "Geçersiz TC numarası."], JSON_UNESCAPED_UNICODE));
}

try {
    $pdo = new PDO("mysql:host=localhost;dbname=gsm;charset=utf8mb4", "root", "");
    
    $stmt = $pdo->prepare("SELECT * FROM `145mgsm` WHERE TC = ?");
    $stmt->execute([$tc]);
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    if (empty($data)) {
        echo json_encode(["success" => false, "message" => "Bulunamadı"], JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(["success" => true, "data" => $data, "footer" => "API-BY-LUNA"], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
} catch (Exception $e) {
    die(json_encode(["error" => "DB Error: " . $e->getMessage()], JSON_UNESCAPED_UNICODE));
}
?>


// ===== 116m/tcgsm-v2.php =====
<?php
// GÜVENLİ TC→GSM SORGUSU (v2)
require_once __DIR__ . '/../config/DatabaseConnection.php';
require_once __DIR__ . '/../config/APIHelper.php';

header('Content-Type: application/json; charset=utf-8');

// TC'yi al ve doğrula
$tc = APIHelper::getParam('tc', '', '/^\d{11}$/');

if (!$tc) {
    APIHelper::error('Geçersiz TC numarası. 11 haneli sayı girin.');
}

try {
    $pdo = DatabaseConnection::getPDO('gsm');
    
    // TC'den GSM bul
    $stmt = $pdo->prepare("SELECT * FROM `145mgsm` WHERE TC = ?");
    $stmt->execute([$tc]);
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    if (empty($data)) {
        APIHelper::response(false, null, 'Bu TC numarasına ait GSM bulunamadı.');
    }
    
    APIHelper::response(true, ['data' => $data], null, 'API-BY-LUNA');
    
} catch (Exception $e) {
    APIHelper::error('Sorgu hatası', $e->getMessage());
}
?>


// ===== 116m/tcgsm.php =====
<?php
error_reporting(E_ALL); // Hataları tümüyle göster
header('Content-Type: application/json');

$host = "localhost";
$user = "root";
$password = "";
$dbname = "gsm";

$conn = mysqli_connect($host, $user, $password, $dbname);

if (!$conn) {
    die(json_encode(array('success' => false, 'error' => 'Bağlantı başarısız: ' . mysqli_connect_error()), JSON_UNESCAPED_UNICODE));
}

mysqli_set_charset($conn, "utf8");

$tc = isset($_GET['tc']) ? $_GET['tc'] : null;

if (!$tc) {
    $hata = array('success' => false, 'error' => 'TC değeri belirtilmemiş');
    echo json_encode($hata, JSON_UNESCAPED_UNICODE);
    exit;
}

// SQL sorgusunun doğru olup olmadığını kontrol edelim
$sql = "SELECT * FROM `145mgsm` WHERE TC = ?";
$stmt = mysqli_prepare($conn, $sql);

if ($stmt === false) {
    // SQL sorgusu hata veriyorsa, hata mesajını gösterelim
    $error = array('success' => false, 'error' => 'SQL sorgusu hatalı: ' . mysqli_error($conn));
    echo json_encode($error, JSON_UNESCAPED_UNICODE);
    exit;
}

mysqli_stmt_bind_param($stmt, 's', $tc); // 's' parametresi string olduğu için
mysqli_stmt_execute($stmt);

$result = mysqli_stmt_get_result($stmt);

// Eğer veri bulunamazsa hata mesajı döndür
if (mysqli_num_rows($result) === 0) {
    $error = array('error' => 'Belirtilen TC numarasına sahip kişi bulunamadı.');
    echo json_encode($error, JSON_UNESCAPED_UNICODE);
} else {
    // Verileri alıp JSON formatında döndürün
    $data = mysqli_fetch_all($result, MYSQLI_ASSOC); // Veriyi dizi olarak al

    $output = [
        "data" => $data
    ];

    echo json_encode($output, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}

mysqli_close($conn);

function checkAuthToken() {
    $auth = isset($_GET['auth']) ? $_GET['auth'] : '';
    if ($auth == "fire") {
        return true;
    } else {
        return false;
    }
}
?>


// ===== 116m/tcgsmdetay.php =====
<?php
header("Content-Type: application/json; charset=utf-8");

// gsm veritabanı bağlantısı (PDO)
try {
    $pdo_gsm = new PDO("mysql:host=localhost;dbname=gsm;charset=utf8mb4", "root", "", [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);
} catch (PDOException $e) {
    die(json_encode(["error" => "GSM veritabanı bağlantı hatası"], JSON_UNESCAPED_UNICODE));
}

// 101m veritabanı bağlantısı (mysqli)
$conn = new mysqli("localhost", "root", "", "101m");
if ($conn->connect_error) {
    die(json_encode(["error" => "101m veritabanı bağlantı hatası"], JSON_UNESCAPED_UNICODE));
}
$conn->set_charset("utf8mb4");

// Parametre kontrolü
if (!isset($_GET['value']) || trim($_GET['value']) === '') {
    die(json_encode(["error" => "Lütfen 'value' parametresi gönderin."], JSON_UNESCAPED_UNICODE));
}

$value = trim($_GET['value']);
$tc = null;

// 1. value TC mi yoksa GSM mi? → TC'yi bul
if (strlen($value) >= 11) {
    // TC olarak geldi
    $stmt = $pdo_gsm->prepare("SELECT TC FROM gsm WHERE TC = ? LIMIT 1");
    $stmt->execute([$value]);
} else {
    // GSM olarak geldi
    $stmt = $pdo_gsm->prepare("SELECT TC FROM gsm WHERE GSM = ? LIMIT 1");
    $stmt->execute([$value]);
}

$row = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$row) {
    die(json_encode(["error" => "Bu TC veya GSM numarasına ait kayıt bulunamadı."], JSON_UNESCAPED_UNICODE));
}

$tc = $row['TC'];

// 2. 101m tablosundan sadece bu TC'ye ait kişiyi çek
$stmt2 = $conn->prepare("SELECT * FROM `101m` WHERE TC = ? LIMIT 1");
$stmt2->bind_param("s", $tc);
$stmt2->execute();
$result = $stmt2->get_result();

if ($result->num_rows === 0) {
    die(json_encode(["error" => "Kişi 101m veritabanında bulunamadı."], JSON_UNESCAPED_UNICODE));
}

$person = $result->fetch_assoc();

// 3. Bu TC'ye ait tüm GSM numaralarını çek
$gsm_stmt = $pdo_gsm->prepare("SELECT GSM FROM gsm WHERE TC = ?");
$gsm_stmt->execute([$tc]);
$gsms = $gsm_stmt->fetchAll(PDO::FETCH_COLUMN);

// Sonuç (sadece şahıs)
$sonuc = [
    "TC"          => $person['TC'],
    "ADI"         => $person['ADI'],
    "SOYADI"      => $person['SOYADI'],
    "DOGUMTARIHI" => $person['DOGUMTARIHI'],
    "NUFUSIL"     => $person['NUFUSIL'],
    "NUFUSILCE"   => $person['NUFUSILCE'],
    "ANNEADI"     => $person['ANNEADI'],
    "ANNETC"      => $person['ANNETC'],
    "BABAADI"     => $person['BABAADI'],
    "BABATC"      => $person['BABATC'],
    "UYRUK"       => $person['UYRUK'] ?? "TR",
    "GSM"         => array_map('strval', $gsms)
];

// Çıktı
echo json_encode([
    "data"   => $sonuc,
    "footer" => "   API-BY-LUNA"
], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

// Kapat
$stmt2->close();
$conn->close();
?>


// ===== 25m/okulno.php =====
<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "25m";

// Veritabanı bağlantısını oluştur
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// API endpoint tanımla
if ($_SERVER['REQUEST_METHOD'] == 'GET' && isset($_GET['tc'])) {
    $tc = $_GET['tc'];
    
    // SQL sorgusunu hazırla
    $sql = "SELECT id, TC, OKULNO, ADI, SOYADI, DURUM FROM okulno WHERE TC = ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("s", $tc);
    $stmt->execute();
    $result = $stmt->get_result();
    
    // Verileri çek ve JSON olarak döndür
    header('Content-Type: application/json');
    if ($result->num_rows > 0) {
        $data = [];
        while ($row = $result->fetch_assoc()) {
            $data[] = [
                'id' => $row['id'],
                'tc' => $row['TC'],
                'okulno' => $row['OKULNO'],
                'adi' => $row['ADI'],
                'soyadi' => $row['SOYADI'],
                'durum' => $row['DURUM']
            ];
        }
        echo json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(["message" => "No results found"], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }
    
    $stmt->close();
} else {
    header('Content-Type: application/json');
    echo json_encode(["message" => "Invalid request. Please provide a 'tc' parameter."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}

$conn->close();
?>


// ===== 6m/multeci.php =====
<?php
header('Content-Type: application/json');

// Database connection configuration
$host = 'localhost';
$db = '6m';
$user = 'root';
$pass = '';
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$options = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $options);
} catch (\PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
    exit;
}

// Check if the TC parameter is set
if (isset($_GET['tc'])) {
    $tc = $_GET['tc'];

    // Prepare and execute the SQL query
    $stmt = $pdo->prepare('SELECT * FROM multeci_6m WHERE TC = ? LIMIT 1');
    $stmt->execute([$tc]);

    // Fetch the result
    $result = $stmt->fetch();

    // Check if a row is found
    if ($result) {
        // Change author value
        $result['author'] = 'API-BY-LUNA';

        // Return the result as formatted JSON
        echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        // Return an error message if no row is found
        echo json_encode(['error' => 'No record found'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }
} else {
    // Return an error message if the TC parameter is not set
    echo json_encode(['error' => 'TC parameter is required'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}
?>


// ===== 81m/adres2024.php =====
<?php
header("Content-Type: application/json");

// Veritabanı bağlantısı
$host = "localhost";
$dbname = "98m";
$username = "root";
$password = ""; // XAMPP için genelde şifre boş olur

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(["error" => "Veritabanına bağlanılamadı.", "detay" => $e->getMessage()]);
    exit;
}

// TC parametresi kontrolü
if (!isset($_GET['tc'])) {
    echo json_encode(["error" => "Lütfen 'tc' parametresi gönderin. Örnek: ?tc=10001000282"]);
    exit;
}

$tc = $_GET['tc'];

// Sorgu
$sql = "SELECT ID, TC, ADRES2024, ADRES2023, ADRES2017, ADRES2015, ADRES2009 FROM `98m` WHERE TC = :tc";
$stmt = $pdo->prepare($sql);
$stmt->execute(['tc' => $tc]);
$data = $stmt->fetch(PDO::FETCH_ASSOC);

if ($data) {
    $json = [
        "ID" => $data["ID"],
        "TC" => $data["TC"],
        "Adresler" => [
            "2024" => $data["ADRES2024"],
            "2023" => $data["ADRES2023"],
            "2017" => $data["ADRES2017"],
            "2015" => $data["ADRES2015"],
            "2009" => $data["ADRES2009"]
        ]
    ];
    echo json_encode($json, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
} else {
    echo json_encode(["error" => "Kayıt bulunamadı."]);
}
?>


// ===== 82m/82m-api-adres.php =====
﻿<?php
// Veritabanı bağlantı bilgileri
$servername = "localhost";
$username = "root";
$password = ""; // MySQL root kullanıcısının şifresi
$dbname = "82m"; // Veritabanı adı

// Veritabanına bağlan
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantıyı kontrol et
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantısı başarısız: " . $conn->connect_error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// API'yi kullanarak sorgulama parametrelerini al
$kimlikNo = $_GET['kimlikNo'] ?? '';

if ($kimlikNo) {
    // KimlikNo parametresine göre veritabanında arama yap
    $stmt = $conn->prepare("SELECT * FROM `datam` WHERE KimlikNo = ?");
    if ($stmt === false) {
        die(json_encode(["error" => "SQL sorgusu hazırlanırken hata oluştu: " . $conn->error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    $stmt->bind_param("s", $kimlikNo);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result === false) {
        die(json_encode(["error" => "SQL sorgusu çalıştırılırken hata oluştu: " . $stmt->error], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    $records = [];
    while ($row = $result->fetch_assoc()) {
        $records[] = $row;
    }

    header('Content-Type: application/json');
    if (empty($records)) {
        echo json_encode(["error" => "Belirtilen kimlik numarasına ait kayıt bulunamadı."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode($records, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }

    // Prepared statement'i kapat
    $stmt->close();
} else {
    echo json_encode(["error" => "Lütfen bir kimlik numarası girin."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}

// Veritabanı bağlantısını kapat
$conn->close();
?>


// ===== 82m/adres-konum - Kopya.php =====
﻿<?php
// Gelen kimlik numarasını al
$kimlikNo = $_GET['kimlikNo'] ?? '';

if ($kimlikNo) {
    // İlk API'nin URL'si
    $apiUrl = "http://localhost/82m/82m-api-adres.php?kimlikNo=" . urlencode($kimlikNo);

    // İlk API'ye istek gönder
    $response = @file_get_contents($apiUrl); // Hata oluşursa @ ile susturuluyor
    if ($response === false) {
        die(json_encode(["error" => "API'ye ulaşılamadı veya bir bağlantı hatası oluştu."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    // JSON yanıtını çözümle
    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        die(json_encode(["error" => "API yanıtı geçerli bir JSON formatında değil."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    // "Ikametgah" bilgisini kontrol et
    if (!empty($data[0]['Ikametgah'])) {
        $ikametgah = $data[0]['Ikametgah'];

        // Google Maps URL'sini oluştur
        $baseUrl = "https://www.google.com/maps/search/";
        $encodedAddress = urlencode($ikametgah);
        $googleMapsUrl = $baseUrl . $encodedAddress . "/@41.0331247,28.4155528,12.02z?hl=tr&entry=ttu&g_ep=EgoyMDI1MDQzMC4xIKXMDSoASAFQAw%3D%3D";

        // Google Maps URL'sini döndür
        header('Content-Type: application/json');
        echo json_encode(["mapsUrl" => $googleMapsUrl], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(["error" => "Ikametgah bilgisi bulunamadı veya boş."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }
} else {
    echo json_encode(["error" => "Lütfen bir kimlik numarası girin."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}
?>


// ===== 82m/adres-konum.php =====
﻿<?php
header('Content-Type: application/json; charset=UTF-8');

// Gelen kimlik numarasını al
$kimlikNo = $_GET['kimlikNo'] ?? '';

if ($kimlikNo) {
    // API'nin URL'si
    $apiUrl = "http://localhost/82m/82m-api-adres.php?kimlikNo=" . urlencode($kimlikNo);

    // API'ye istek gönder
    $response = @file_get_contents($apiUrl);

    if ($response === false) {
        die(json_encode([
            "error" => "API'ye ulaşılamadı veya bir bağlantı hatası oluştu."
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    // UTF-8 BOM varsa temizle
    $response = preg_replace('/^\xEF\xBB\xBF/', '', $response);

    // JSON yanıtını çözümle
    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        die(json_encode([
            "error" => "API yanıtı geçerli bir JSON formatında değil.",
            "json_error" => json_last_error_msg(),
            "raw_response" => $response
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    // "Ikametgah" bilgisini kontrol et
    if (!empty($data[0]['Ikametgah'])) {
        $ikametgah = $data[0]['Ikametgah'];

        // Google Maps URL'sini oluştur
        $baseUrl = "https://www.google.com/maps/search/";
        $encodedAddress = urlencode($ikametgah);
        $googleMapsUrl = $baseUrl . $encodedAddress . "/@41.0331247,28.4155528,12.02z?hl=tr&entry=ttu";

        // Google Maps URL'sini döndür (tıklanabilir halde)
        echo json_encode([
            "mapsUrl" => $googleMapsUrl
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    } else {
        echo json_encode([
            "error" => "Ikametgah bilgisi bulunamadı veya boş."
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }
} else {
    echo json_encode([
        "error" => "Lütfen bir kimlik numarası girin."
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}
?>


// ===== 82m/adres-konumm.php =====
// Gelen kimlik numarasını al
$kimlikNo = $_GET['kimlikNo'] ?? '';

if ($kimlikNo) {
    // İlk API'nin URL'si
    $apiUrl = "http://localhost/82m/82m-api-adres.php?kimlikNo=" . urlencode($kimlikNo);

    // İlk API'ye istek gönder
    $response = @file_get_contents($apiUrl); // Hata oluşursa @ ile susturuluyor
    if ($response === false) {
        die(json_encode(["error" => "API'ye ulaşılamadı veya bir bağlantı hatası oluştu."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    // JSON yanıtını çözümle
    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        die(json_encode(["error" => "API yanıtı geçerli bir JSON formatında değil."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }

    // "Ikametgah" bilgisini kontrol et
    if (!empty($data[0]['Ikametgah'])) {
        $ikametgah = $data[0]['Ikametgah'];

        // Sonundaki boşluk ve rakamları kaldır
        $ikametgah = preg_replace('/\s*\d+$/', '', $ikametgah);

        // Google Maps URL'sini oluştur
        $baseUrl = "https://www.google.com/maps/search/";
        $encodedAddress = urlencode($ikametgah);
        $googleMapsUrl = $baseUrl . $encodedAddress . "/@41.0331247,28.4155528,12.02z?hl=tr&entry=ttu&g_ep=EgoyMDI1MDQzMC4xIKXMDSoASAFQAw%3D%3D";

        // Google Maps URL'sini döndür
        header('Content-Type: application/json');
        echo json_encode(["mapsUrl" => $googleMapsUrl], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(["error" => "Ikametgah bilgisi bulunamadı veya boş."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }
} else {
    echo json_encode(["error" => "Lütfen bir kimlik numarası girin."], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}


// ===== config/APIHelper.php =====
<?php
/**
 * API Yardımcı Sınıfı
 * JSON yanıtları, veri temizliği ve hata yönetimi
 */

class APIHelper {
    /**
     * JSON yanıtı döndür
     */
    public static function response($success, $data = null, $message = null, $footer = null) {
        header('Content-Type: application/json; charset=utf-8');
        
        $response = [
            "success" => $success,
        ];
        
        if ($message) {
            $response["message"] = $message;
        }
        
        if ($data !== null) {
            $response["data"] = $data;
        }
        
        if ($footer) {
            $response["footer"] = $footer;
        }
        
        echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
        exit;
    }
    
    /**
     * Error yanıtı döndür
     */
    public static function error($message, $details = null) {
        header('Content-Type: application/json; charset=utf-8');
        
        $response = [
            "error" => $message
        ];
        
        if ($details && !empty($_GET['debug'] ?? false)) {
            $response["details"] = $details;
        }
        
        echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
        exit;
    }
    
    /**
     * GET parametresi al ve temizle
     */
    public static function getParam($name, $default = "", $pattern = null) {
        $value = isset($_GET[$name]) ? trim($_GET[$name]) : $default;
        
        if ($value && $pattern && !preg_match($pattern, $value)) {
            return null;
        }
        
        return $value;
    }
    
    /**
     * Veri satırını temizle ve null değerleri işle
     */
    public static function cleanRow($row, $defaults = []) {
        $cleaned = [];
        
        if (is_array($row)) {
            foreach ($row as $key => $value) {
                $cleaned[$key] = !empty($value) ? $value : ($defaults[$key] ?? null);
            }
        }
        
        return $cleaned;
    }
    
    /**
     * Tablo sütunlarını seç
     */
    public static function selectColumns($row, $columns = []) {
        $result = [];
        
        foreach ($columns as $col) {
            $result[$col] = $row[$col] ?? null;
        }
        
        return $result;
    }
}
?>


// ===== config/DatabaseConnection.php =====
<?php
/**
 * Merkez Veritabanı Bağlantı Sınıfı
 * Tüm API dosyalarının kullanması için
 */

class DatabaseConnection {
    private static $connections = [];
    
    /**
     * MySQLi bağlantısı al
     * @param string $dbname - Veritabanı adı
     * @return mysqli
     */
    public static function getMysqli($dbname = "101m") {
        $key = "mysqli_" . $dbname;
        
        if (!isset(self::$connections[$key])) {
            $conn = new mysqli("localhost", "root", "", $dbname);
            
            if ($conn->connect_error) {
                die(json_encode([
                    "error" => "Veritabanı bağlantısı başarısız",
                    "details" => $conn->connect_error
                ], JSON_UNESCAPED_UNICODE));
            }
            
            $conn->set_charset("utf8mb4");
            self::$connections[$key] = $conn;
        }
        
        return self::$connections[$key];
    }
    
    /**
     * PDO bağlantısı al
     * @param string $dbname - Veritabanı adı
     * @return PDO
     */
    public static function getPDO($dbname = "101m") {
        $key = "pdo_" . $dbname;
        
        if (!isset(self::$connections[$key])) {
            try {
                $pdo = new PDO(
                    "mysql:host=localhost;dbname=$dbname;charset=utf8mb4",
                    "root",
                    "",
                    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
                );
                self::$connections[$key] = $pdo;
            } catch (PDOException $e) {
                die(json_encode([
                    "error" => "Veritabanı bağlantısı başarısız",
                    "details" => $e->getMessage()
                ], JSON_UNESCAPED_UNICODE));
            }
        }
        
        return self::$connections[$key];
    }
    
    /**
     * Tüm bağlantıları kapat
     */
    public static function closeAll() {
        foreach (self::$connections as $conn) {
            if ($conn instanceof mysqli) {
                $conn->close();
            } elseif ($conn instanceof PDO) {
                $conn = null;
            }
        }
        self::$connections = [];
    }
}
?>


// ===== iban/iban - Kopya.php =====
<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$response = [
    'success' => false,
    'data' => null,
    'error' => null
];

if (!isset($_GET['iban']) && !isset($_POST['iban'])) {
    http_response_code(400);
    $response['error'] = 'IBAN parametresi gerekli';
    echo json_encode($response);
    exit;
}

$iban = trim($_GET['iban'] ?? $_POST['iban']);

if (empty($iban)) {
    http_response_code(400);
    $response['error'] = 'IBAN boş olamaz';
    echo json_encode($response);
    exit;
}

// Query the external API
$url = "https://hesapno.com/cozumleme_iban.php";
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, "iban=" . urlencode($iban));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);

$result = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode !== 200 || !$result) {
    http_response_code(500);
    $response['error'] = 'Dış API\'ye erişim başarısız';
    echo json_encode($response);
    exit;
}

// Parse HTML response
$data = [
    'iban' => $iban
];

// Extract bank info
if (preg_match('/Ad:\s*(.+?)<br/i', $result, $m)) $data['banka']['ad'] = trim(strip_tags($m[1]));
if (preg_match('/Kod:\s*(.+?)<br/i', $result, $m)) $data['banka']['kod'] = trim(strip_tags($m[1]));
if (preg_match('/Swift:\s*(.+?)<br/i', $result, $m)) $data['banka']['swift'] = trim(strip_tags($m[1]));
if (preg_match('/Hesap\s+No:\s*(.+?)<br/i', $result, $m)) $data['banka']['hesap_no'] = trim(strip_tags($m[1]));

// Extract branch info - find after ŞUBE BİLGİLERİ
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Ad:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['ad'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Kod:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['kod'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>İl:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['il'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>İlçe:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['ilce'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Tel:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['tel'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Fax:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['fax'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Adres:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['adres'] = trim($m[1]);

$response['success'] = true;
$response['data'] = $data;
http_response_code(200);
echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>


// ===== iban/iban.php =====
<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$response = [
    'success' => false,
    'data' => null,
    'error' => null
];

if (!isset($_GET['iban']) && !isset($_POST['iban'])) {
    http_response_code(400);
    $response['error'] = 'IBAN parametresi gerekli';
    echo json_encode($response);
    exit;
}

$iban = trim($_GET['iban'] ?? $_POST['iban']);

if (empty($iban)) {
    http_response_code(400);
    $response['error'] = 'IBAN boş olamaz';
    echo json_encode($response);
    exit;
}

// Query the external API
$url = "https://hesapno.com/cozumleme_iban.php";
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, "iban=" . urlencode($iban));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);

$result = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode !== 200 || !$result) {
    http_response_code(500);
    $response['error'] = 'Dış API\'ye erişim başarısız';
    echo json_encode($response);
    exit;
}

// Parse HTML response
$data = [
    'iban' => $iban
];

// Extract bank info
if (preg_match('/Ad:\s*(.+?)<br/i', $result, $m)) $data['banka']['ad'] = trim(strip_tags($m[1]));
if (preg_match('/Kod:\s*(.+?)<br/i', $result, $m)) $data['banka']['kod'] = trim(strip_tags($m[1]));
if (preg_match('/Swift:\s*(.+?)<br/i', $result, $m)) $data['banka']['swift'] = trim(strip_tags($m[1]));
if (preg_match('/Hesap\s+No:\s*(.+?)<br/i', $result, $m)) $data['banka']['hesap_no'] = trim(strip_tags($m[1]));

// Extract branch info - find after ŞUBE BİLGİLERİ
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Ad:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['ad'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Kod:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['kod'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>İl:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['il'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>İlçe:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['ilce'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Tel:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['tel'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Fax:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['fax'] = trim($m[1]);
if (preg_match('/ŞUBE\s+BİLGİLERİ.+?<b>Adres:<\/b>\s*([^<]+)<br/is', $result, $m)) $data['sube']['adres'] = trim($m[1]);

$response['success'] = true;
$response['data'] = $data;
http_response_code(200);
echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>


// ===== isyeri/işyeriyt.php =====
﻿<?php
header("Content-Type: application/json; charset=UTF-8");

// Veritabanı bağlantısı
$servername = "localhost";
$username = "root"; // MySQL kullanıcı adı
$password = ""; // MySQL şifresi (Varsayılan olarak boş)
$database = "isyeri";

$conn = new mysqli($servername, $username, $password, $database);

// Bağlantı kontrolü
if ($conn->connect_error) {
    die(json_encode(["error" => "Veritabanı bağlantı hatası: " . $conn->connect_error]));
}

// TC kimlik numarası al
if (!isset($_GET['tc']) || empty($_GET['tc'])) {
    echo json_encode(["error" => "Lütfen bir TC kimlik numarası girin."]);
    exit;
}

$tc = $conn->real_escape_string($_GET['tc']);

// Sorguyu hazırla ve çalıştır
$sql = "SELECT * FROM sgkyetki WHERE yetkiliTckn = '$tc'";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    $data = [];

    while ($row = $result->fetch_assoc()) {
        $data[] = [
            "ID" => $row["_id"],
            "AdSoyad" => $row["yetkiliAdSoyad"],
            "YetkiTuru" => $row["yetkiTuru"],
            "İşyeriUnvanı" => $row["isyeriUnvani"],
            "SGK_Sicil_No" => $row["sgkSicilNo"],
            "YetkililikDurumu" => $row["yetkililikDurumu"]
        ];
    }

    echo json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
} else {
    echo json_encode(["error" => "Belirtilen TC kimlik numarasına ait kayıt bulunamadı."]);
}

// Bağlantıyı kapat
$conn->close();
?>


// ===== papara/papara.php =====
﻿<?php
// Database configuration
$servername = "127.0.0.1";
$username = "root"; // Default username for XAMPP
$password = ""; // Default password for XAMPP
$dbname = "papara";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Set the content type to application/json and charset to UTF-8
header('Content-Type: application/json; charset=utf-8');

// Get the paparano from the request
$paparano = isset($_GET['paparano']) ? intval($_GET['paparano']) : 0;

if ($paparano > 0) {
    // Prepare and execute the query
    $stmt = $conn->prepare("SELECT id, paparano, adsoyad FROM papara WHERE paparano = ?");
    $stmt->bind_param("i", $paparano);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        // Fetch the result as an associative array
        $row = $result->fetch_assoc();
        
        // Format the response
        $response = [
            "PAPARA NO" => $row['paparano'],
            "İSİM SOY İSİM" => $row['adsoyad']
        ];
        
        // Return the result as JSON
        echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    } else {
        // Return an empty JSON object if no result is found
        echo json_encode([]);
    }

    // Close the statement
    $stmt->close();
} else {
    // Return an error message if the paparano is not provided or invalid
    echo json_encode(["error" => "Invalid or missing paparano"]);
}

// Close the connection
$conn->close();
?>


// ===== plaka/plaka.php =====
﻿<?php
// Database configuration
$servername = "127.0.0.1";
$username = "root"; // Default username for XAMPP
$password = ""; // Default password for XAMPP
$dbname = "75k_plaka";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Set the content type to application/json and charset to UTF-8
header('Content-Type: application/json; charset=utf-8');

// Get the Plaka_No from the request
$plaka_no = isset($_GET['Plaka_No']) ? $_GET['Plaka_No'] : '';

if (!empty($plaka_no)) {
    // Prepare and execute the query
    $stmt = $conn->prepare("SELECT Plaka_No, Isim FROM 75k_plaka WHERE Plaka_No = ?");
    $stmt->bind_param("s", $plaka_no);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        // Fetch the result as an associative array
        $row = $result->fetch_assoc();
        
        // Format the response
        $response = [
            "PLAKA" => $row['Plaka_No'],
            "AD SOYAD" => $row['Isim']
        ];
        
        // Return the result as JSON
        echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    } else {
        // Return an empty JSON object if no result is found
        echo json_encode([]);
    }

    // Close the statement
    $stmt->close();
} else {
    // Return an error message if the Plaka_No is not provided or invalid
    echo json_encode(["error" => "Invalid or missing Plaka_No"]);
}

// Close the connection
$conn->close();
?>


// ===== plaka/plakaceza.php =====
<?php 
header('Content-Type: application/json');

error_reporting(0);

$plaka = $_GET['plaka'];
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, "https://ccis.cordisnetwork.com/CWC/bridgeDebt");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_HTTPGET, 1);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 0);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);
curl_setopt($ch, CURLOPT_USERAGENT, "Mozilla/5.0 (Linux; Android 11; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36");
curl_setopt($ch, CURLOPT_POSTFIELDS,
            "query=plakatabtoplamborc&PlateNumber=$plaka&IsTotalDebtQuery=1&Hash=99331");

$resp = curl_exec($ch);
$resp = preg_replace('/lang="tr"[\s\S]+?td style="height:5px;"/', '', $resp);
$resp = str_replace("</html>", "verxnqwe", $resp);
$resp = preg_replace('/tbody[\s\S]+?verxnqwe/', '', $resp);
$resp = str_replace('<html ></td>', "basla", $resp);
$resp = preg_replace('/basla[\s\S]+?style="height:5px;"/', '', $resp);
$resp = str_replace('></td>
                    </tr>', "basladık", $resp);
$resp = str_replace('<td style="height:5px;"basladık
                </', "", $resp);
$resp = str_replace('basladık', "", $resp);
$resp = str_replace('<!DOCTYPE html>', "", $resp);
$resp = str_replace("<tr class='printtr'>", "", $resp);
$resp = str_replace('<tr>', "", $resp);
$resp = str_replace('</tr>', "", $resp);

$resp = str_replace('> <', ">-<", $resp);
$resp = str_replace('><', ">-<", $resp);
preg_match_all('@<td class="textStyle" >(.*?)</td>@', $resp, $resp);

$plaka = $plaka;
$borcturu = $resp[1][0];
$isimsoyisim = $resp[1][7];
$tc = $resp[1][8];
$buro = $resp[1][9];
$burotel = $resp[1][10];
$ceza = $resp[1][5];
$toplamceza = $resp[1][11];


$result = array(
    array(
        "owner" => "Luna", 
        "data" => array(
            "plaka" => $plaka,
            "borcturu" => $borcturu,
            "adsoyad" => $isimsoyisim,
            "tc" => $tc,
            "buro" => $buro,
            "burotelefon" => $burotel,
            "yazilanceza" => $ceza,
            "toplamceza" => $toplamceza
        )
    )
);
echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>


// ===== sgk/calisan.php =====
<?php
header('Content-Type: application/json');

$host = "localhost";
$dbname = "sgk";
$user = "root";
$password = "";

try {
    $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(['error' => 'Veritabanı bağlantısı başarısız: ' . $e->getMessage()]);
    exit;
}

function sanitize_output($data) {
    return htmlspecialchars($data, ENT_QUOTES, 'UTF-8');
}

$tc = isset($_GET['tc']) ? strip_tags($_GET['tc']) : '';

if (empty($tc) || !preg_match('/^\d{11}$/', $tc)) {
    $hata = array('success' => false, 'message' => 'Lütfen 11 haneli geçerli bir TC kimlik numarası giriniz');
    echo json_encode($hata, JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    // 1. Verilen TC'ye göre çalışanın isyeriId ve isyeriUnvani alınıyor
    $sql1 = "SELECT isyeriId, isyeriUnvani FROM theos WHERE calisanKimlikNo = :tc LIMIT 1";
    $stmt1 = $conn->prepare($sql1);
    $stmt1->bindParam(':tc', $tc, PDO::PARAM_STR);
    $stmt1->execute();

    if ($stmt1->rowCount() == 0) {
        echo json_encode(['success' => false, 'message' => 'Çalışan bulunamadı'], JSON_UNESCAPED_UNICODE);
        exit;
    }

    $result = $stmt1->fetch(PDO::FETCH_ASSOC);
    $isyeriId = $result['isyeriId'];
    $isyeriUnvani = $result['isyeriUnvani'];

    // 2. Aynı işyeriId'ye bağlı tüm çalışanları çekiyoruz
    $sql2 = "SELECT * FROM theos WHERE isyeriId = :isyeriId ORDER BY calisanAdSoyad ASC";
    $stmt2 = $conn->prepare($sql2);
    $stmt2->bindParam(':isyeriId', $isyeriId, PDO::PARAM_STR);
    $stmt2->execute();

    $calisanlar = $stmt2->fetchAll(PDO::FETCH_ASSOC);

    // 3. Her çalışanın verisini sanitize ediyoruz ve sıralama numarası ekliyoruz
    foreach ($calisanlar as $index => &$calisan) {
        foreach ($calisan as $key => $value) {
            $calisan[$key] = sanitize_output($value) ?: 'Bulunamadı';
        }
        $calisan['sira'] = $index + 1;
    }

    $response = [
        'success' => true,
        'total_calisan' => count($calisanlar),
        'isyeriUnvani' => sanitize_output($isyeriUnvani),
        'data' => $calisanlar
    ];

    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (PDOException $e) {
    echo json_encode(['error' => 'Sorgu hatası: ' . $e->getMessage()]);
}

$conn = null;
?>


// ===== sgk/calısan.php =====
<?php
header('Content-Type: application/json');

$host = "localhost";
$dbname = "sgk";
$user = "root";
$password = "";

try {
    $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(['error' => 'Veritabanı bağlantısı başarısız: ' . $e->getMessage()]);
    exit;
}

function sanitize_output($data) {
    return htmlspecialchars($data, ENT_QUOTES, 'UTF-8');
}

$tc = isset($_GET['tc']) ? strip_tags($_GET['tc']) : '';

if (empty($tc) || !preg_match('/^\d{11}$/', $tc)) {
    $hata = array('success' => false, 'message' => 'Lütfen 11 haneli geçerli bir TC kimlik numarası giriniz');
    echo json_encode($hata, JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    // 1. Verilen TC'ye göre çalışanın isyeriId ve isyeriUnvani alınıyor
    $sql1 = "SELECT isyeriId, isyeriUnvani FROM theos WHERE calisanKimlikNo = :tc LIMIT 1";
    $stmt1 = $conn->prepare($sql1);
    $stmt1->bindParam(':tc', $tc, PDO::PARAM_STR);
    $stmt1->execute();

    if ($stmt1->rowCount() == 0) {
        echo json_encode(['success' => false, 'message' => 'Çalışan bulunamadı'], JSON_UNESCAPED_UNICODE);
        exit;
    }

    $result = $stmt1->fetch(PDO::FETCH_ASSOC);
    $isyeriId = $result['isyeriId'];
    $isyeriUnvani = $result['isyeriUnvani'];

    // 2. Aynı işyeriId'ye bağlı tüm çalışanları çekiyoruz
    $sql2 = "SELECT * FROM theos WHERE isyeriId = :isyeriId ORDER BY calisanAdSoyad ASC";
    $stmt2 = $conn->prepare($sql2);
    $stmt2->bindParam(':isyeriId', $isyeriId, PDO::PARAM_STR);
    $stmt2->execute();

    $calisanlar = $stmt2->fetchAll(PDO::FETCH_ASSOC);

    // 3. Her çalışanın verisini sanitize ediyoruz ve sıralama numarası ekliyoruz
    foreach ($calisanlar as $index => &$calisan) {
        foreach ($calisan as $key => $value) {
            $calisan[$key] = sanitize_output($value) ?: 'Bulunamadı';
        }
        $calisan['sira'] = $index + 1;
    }

    $response = [
        'success' => true,
        'total_calisan' => count($calisanlar),
        'isyeriUnvani' => sanitize_output($isyeriUnvani),
        'data' => $calisanlar
    ];

    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (PDOException $e) {
    echo json_encode(['error' => 'Sorgu hatası: ' . $e->getMessage()]);
}

$conn = null;
?>


// ===== sgk/sgk.php =====
<?php
header('Content-Type: application/json');

$host = "localhost";
$dbname = "sgk";
$user = "root";
$password = "";

try {
    $conn = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo json_encode(['error' => 'Veritabanı bağlantısı başarısız: ' . $e->getMessage()]);
    exit;
}

function sanitize_output($data) {
    return htmlspecialchars($data, ENT_QUOTES, 'UTF-8');
}

$tc = isset($_GET['tc']) ? strip_tags($_GET['tc']) : '';

if (empty($tc) || !preg_match('/^\d{11}$/', $tc)) {
    $hata = array('success' => false, 'message' => 'Lütfen 11 haneli geçerli bir TC kimlik numarası giriniz');
    echo json_encode($hata, JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    $sql = "SELECT * FROM theos WHERE calisanKimlikNo = :tc";
    $stmt = $conn->prepare($sql);
    $stmt->bindParam(':tc', $tc, PDO::PARAM_STR);
    $stmt->execute();
    
    $data = array();
    if ($stmt->rowCount() > 0) {
        $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
        foreach ($data as &$employee) {
            foreach ($employee as $key => $value) {
                $employee[$key] = sanitize_output($value) ?: 'Bulunamadı';
            }
        }
        echo json_encode(['success' => true, 'data' => $data], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(['success' => false, 'message' => 'Çalışan bulunamadı'], JSON_UNESCAPED_UNICODE);
    }

} catch (PDOException $e) {
    echo json_encode(['error' => 'Sorgu hatası: ' . $e->getMessage()]);
}

$conn = null;
?>


// ===== tapu/adaparsel-il-ilce.php =====
<?php
// CORS Headers
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

// Timeout ve performance ayarları
set_time_limit(180);
ini_set('default_socket_timeout', 180);

// Parametreleri al - Support both single and separate parameter formats
$adaParselIlIlce = isset($_GET['ada']) ? $_GET['ada'] : null;

if ($adaParselIlIlce && strpos($adaParselIlIlce, '-') !== false) {
    // Old format: ada=20905-2-ANKARA or ada=20905-2-ANKARA-ALTINDAĞ
    $parts = explode('-', $adaParselIlIlce);
    if (count($parts) < 2 || count($parts) > 4) {
        http_response_code(400);
        die(json_encode([
            "status" => "error",
            "code" => 400,
            "error" => "Lütfen geçerli bir değer sağlayın. Örnek: ?ada=20905-2 veya ?ada=20905-2-ANKARA veya ?ada=20905-2-ANKARA-ALTINDAĞ"
        ], JSON_UNESCAPED_UNICODE));
    }
    $ada = (int)preg_replace('/[^0-9]/', '', $parts[0]);
    $parsel = (int)preg_replace('/[^0-9]/', '', $parts[1]);
    $il = isset($parts[2]) ? trim(strtoupper($parts[2])) : null;
    $ilce = isset($parts[3]) ? trim(strtoupper($parts[3])) : null;
} else {
    // New format: separate parameters
    $ada = isset($_GET['ada']) ? (int)preg_replace('/[^0-9]/', '', $_GET['ada']) : null;
    $parsel = isset($_GET['parsel']) ? (int)preg_replace('/[^0-9]/', '', $_GET['parsel']) : null;
    $il = isset($_GET['il']) ? trim(strtoupper($_GET['il'])) : null;
    $ilce = isset($_GET['ilce']) ? trim(strtoupper($_GET['ilce'])) : null;
}

// Validation
if (!$ada || !$parsel) {
    http_response_code(400);
    die(json_encode([
        "status" => "error",
        "code" => 400,
        "error" => "ada ve parsel zorunlu"
    ], JSON_UNESCAPED_UNICODE));
}

try {
    $pdo = new PDO("mysql:host=localhost;dbname=tapu;charset=utf8mb4", "root", "");
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Base query - direct integer comparison
    $sql = "SELECT 
                id, 
                il, 
                ilce, 
                MahalleKoyAdi AS 'Mahalle/Köy', 
                ZeminTip AS 'Zemin Tipi', 
                Ada, 
                Parsel, 
                CONCAT(Yuzolcum, ' m²') AS 'Yüzölçüm', 
                AnaTasinmazNitelik AS 'Nitelik', 
                Adi AS 'Adı', 
                Soyadi AS 'Soyadı', 
                BabaAdi AS 'Baba Adı', 
                TCKimlikNo AS 'TC Kimlik No', 
                EdinmeSebebi AS 'Edinme Sebebi', 
                CASE 
                    WHEN Tarih IS NOT NULL THEN Tarih
                    ELSE 'None'
                END AS Tarih, 
                Yevmiye
            FROM tapu 
            WHERE Ada = ? AND Parsel = ?";
    $params = [$ada, $parsel];
    
    // Optional filters - only add if not empty/null
    if (!empty($il)) {
        $sql .= " AND UPPER(TRIM(il)) = ?";
        $params[] = $il;
    }
    if (!empty($ilce)) {
        $sql .= " AND UPPER(TRIM(ilce)) = ?";
        $params[] = $ilce;
    }
    
    $sql .= " LIMIT 100";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    if (!$results) {
        http_response_code(404);
        die(json_encode([
            "status" => "error",
            "code" => 404,
            "error" => "Kayıt bulunamadı"
        ], JSON_UNESCAPED_UNICODE));
    }
    
    echo json_encode([
        "status" => "success",
        "code" => 200,
        "data" => $results
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    
} catch (Exception $e) {
    http_response_code(500);
    die(json_encode([
        "status" => "error",
        "code" => 500,
        "error" => $e->getMessage()
    ], JSON_UNESCAPED_UNICODE));
}

$pdo = null;
?>


// ===== tapu/adaparsel.php =====
﻿<?php
// Veritabanı bağlantısı için gerekli bilgiler
$servername = "localhost";
$username = "root"; // Veritabanı kullanıcı adı
$password = ""; // Veritabanı şifresi
$dbname = "tapu"; // Veritabanı adı

// JSON çıktısı için Content-Type başlığı ayarlanıyor
header('Content-Type: application/json; charset=utf-8');

// Ada ve parsel bilgilerini tek bir parametreden (ada) al
$adaParsel = isset($_GET['ada']) ? $_GET['ada'] : null;

// Eğer gerekli parametre eksikse hata mesajı gönder
if (!$adaParsel) {
    http_response_code(400); // Bad Request
    echo json_encode([
        "error" => "Lütfen 'ada' parametresini sağlayın. Örnek: ?ada=186-1"
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// Ada ve parseli ayır
$adaParselParts = explode('-', $adaParsel);

// Eğer ada veya parsel eksikse hata mesajı gönder
if (count($adaParselParts) !== 2 || empty($adaParselParts[0]) || empty($adaParselParts[1])) {
    http_response_code(400); // Bad Request
    echo json_encode([
        "error" => "Lütfen geçerli bir 'ada-parsel' değeri sağlayın. Örnek: ?ada=186-1"
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

$ada = $adaParselParts[0];
$parsel = $adaParselParts[1];

try {
    // Veritabanı bağlantısını oluştur
    $conn = new PDO("mysql:host=$servername;dbname=$dbname;charset=utf8mb4", $username, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Veritabanında ada ve parsel kombinasyonu için sorgu
    $stmt = $conn->prepare("
        SELECT 
            id, 
            il, 
            ilce, 
            MahalleKoyAdi, 
            ZeminTip, 
            Ada, 
            Parsel, 
            Yuzolcum, 
            AnaTasinmazNitelik, 
            Adi, 
            Soyadi, 
            BabaAdi, 
            TCKimlikNo, 
            EdinmeSebebi, 
            CASE 
                WHEN Tarih IS NOT NULL THEN DATE_FORMAT(Tarih, '%d/%m/%Y') 
                ELSE NULL 
            END AS Tarih, 
            Yevmiye 
        FROM tapu 
        WHERE Ada = :ada AND Parsel = :parsel
    ");
    $stmt->bindParam(':ada', $ada, PDO::PARAM_STR);
    $stmt->bindParam(':parsel', $parsel, PDO::PARAM_STR);

    // Sorguyu çalıştır
    $stmt->execute();

    // Sonuçları al ve JSON formatına çevir
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

    if ($results) {
        // Verilerin istenen formatta döndüğünden emin olun
        $formattedResults = array_map(function ($row) {
            return [
                "id" => (int)$row["id"],
                "il" => $row["il"],
                "ilce" => $row["ilce"],
                "MahalleKoyAdi" => $row["MahalleKoyAdi"],
                "ZeminTip" => $row["ZeminTip"],
                "Ada" => $row["Ada"],
                "Parsel" => $row["Parsel"],
                "Yuzolcum" => $row["Yuzolcum"],
                "AnaTasinmazNitelik" => $row["AnaTasinmazNitelik"],
                "Adi" => $row["Adi"],
                "Soyadi" => $row["Soyadi"],
                "BabaAdi" => $row["BabaAdi"],
                "TCKimlikNo" => $row["TCKimlikNo"],
                "EdinmeSebebi" => $row["EdinmeSebebi"],
                "Tarih" => $row["Tarih"], // Eğer null ise null olarak döner
                "Yevmiye" => $row["Yevmiye"]
            ];
        }, $results);

        // JSON_UNESCAPED_UNICODE ile Türkçe karakterlerin doğru şekilde döndürülmesini sağlıyoruz.
        // JSON_PRETTY_PRINT ile düzenli bir görünüm sağlıyoruz.
        echo json_encode($formattedResults, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    } else {
        http_response_code(404); // Not Found
        echo json_encode([
            "error" => "Belirtilen ada ve parsel bilgileriyle eşleşen kayıt bulunamadı."
        ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
} catch (PDOException $e) {
    http_response_code(500); // Internal Server Error
    echo json_encode([
        "error" => "Veritabanı hatası: " . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
}

// Veritabanı bağlantısını kapat
$conn = null;
?>


// ===== tapu/tapuadsoyad.php =====
﻿<?php
// Veritabanı bağlantısı
$servername = "localhost";
$username = "root"; // Veritabanı kullanıcı adı
$password = ""; // Veritabanı şifresi
$dbname = "tapu"; // Veritabanı adı

// Bağlantıyı kurma
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantı kontrolü
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Ad ve Soyad'ı al
$adi = isset($_GET['adi']) ? $_GET['adi'] : '';
$soyadi = isset($_GET['soyadi']) ? $_GET['soyadi'] : '';

// Eğer Ad ve Soyad yoksa, hata mesajı döndür
if (empty($adi) || empty($soyadi)) {
    echo json_encode(["error" => "Ad ve Soyad girilmelidir."]);
    exit;
}

// SQL sorgusu: sadece aranan kişinin (Ad ve Soyad) verisini alıyoruz
$sql = "SELECT * FROM tapu WHERE Adi = '$adi' AND Soyadi = '$soyadi' LIMIT 1"; // Limit 1 ekleyerek sadece ilk bulduğumuzu alıyoruz

// Sorguyu çalıştır
$result = $conn->query($sql);

// Sonuç kontrolü
if ($result->num_rows > 0) {
    // Kayıt döndü
    $row = $result->fetch_assoc();
    $data = [
        'id' => $row['id'],
        'il' => $row['il'],
        'ilce' => $row['ilce'],
        'MahalleKoyAdi' => $row['MahalleKoyAdi'],
        'ZeminTip' => $row['ZeminTip'],
        'Ada' => $row['Ada'],
        'Parsel' => $row['Parsel'],
        'Yuzolcum' => $row['Yuzolcum'],
        'AnaTasinmazNitelik' => $row['AnaTasinmazNitelik'],
        'Adi' => $row['Adi'],
        'Soyadi' => $row['Soyadi'],
        'BabaAdi' => $row['BabaAdi'],
        'TCKimlikNo' => $row['TCKimlikNo'],
        'EdinmeSebebi' => $row['EdinmeSebebi'],
        // Tarihi formatı düzelt
        'Tarih' => str_replace('/', '-', $row['Tarih']),
        'Yevmiye' => $row['Yevmiye']
    ];

    // JSON verisini düzgün formatta döndür
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
} else {
    echo json_encode(["error" => "No records found for this Ad and Soyad."]);
}

// Bağlantıyı kapatma
$conn->close();
?>


// ===== tapu/taputc.php =====
﻿<?php
// Veritabanı bağlantısı
$servername = "localhost";
$username = "root"; // Veritabanı kullanıcı adı
$password = ""; // Veritabanı şifresi
$dbname = "tapu"; // Veritabanı adı

// Bağlantıyı kurma
$conn = new mysqli($servername, $username, $password, $dbname);

// Bağlantı kontrolü
if ($conn->connect_error) {
    die(json_encode(["error" => "Connection failed: " . $conn->connect_error]));
}

// TC Kimlik numarasını al
$tc = isset($_GET['tc']) ? $_GET['tc'] : '';

// Eğer TC yoksa, hata mesajı döndür
if (empty($tc)) {
    echo json_encode(["error" => "TC kimlik numarası girilmelidir."]);
    exit;
}

// SQL sorgusu
$sql = "SELECT * FROM tapu WHERE TCKimlikNo = ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param("s", $tc);
$stmt->execute();
$result = $stmt->get_result();

// Sonuçları JSON olarak döndür
if ($result->num_rows > 0) {
    $data = [];

    while ($row = $result->fetch_assoc()) {
        $data[] = [
            'id' => $row['id'],
            'il' => $row['il'],
            'ilce' => $row['ilce'],
            'MahalleKoyAdi' => $row['MahalleKoyAdi'],
            'ZeminTip' => $row['ZeminTip'],
            'Ada' => $row['Ada'],
            'Parsel' => $row['Parsel'],
            'Yuzolcum' => $row['Yuzolcum'],
            'AnaTasinmazNitelik' => $row['AnaTasinmazNitelik'],
            'Adi' => $row['Adi'],
            'Soyadi' => $row['Soyadi'],
            'BabaAdi' => $row['BabaAdi'],
            'TCKimlikNo' => $row['TCKimlikNo'],
            'EdinmeSebebi' => $row['EdinmeSebebi'],
            'Tarih' => str_replace('/', '-', $row['Tarih']),
            'Yevmiye' => $row['Yevmiye']
        ];
    }

    // JSON verisini düzgün formatta döndür
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
} else {
    echo json_encode(["error" => "No records found for this TC."]);
}

// Bağlantıyı kapatma
$stmt->close();
$conn->close();
?>


// ===== ttnet/ttnet.php =====
<?php
header('Content-Type: application/json');

$host = 'localhost';
$db = 'ttnet';
$user = 'root';
$pass = '';
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$options = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $options);
} catch (\PDOException $e) {
    echo json_encode(["status" => "error", "message" => "Connection failed: " . $e->getMessage()], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    exit;
}

if (isset($_GET['gsm'])) {
    $gsm = preg_replace('/\D/', '', $_GET['gsm']); // Remove all non-digit characters
    $stmt = $pdo->prepare("SELECT * FROM ttnet WHERE REPLACE(REPLACE(REPLACE(GSM, ' ', ''), '-', ''), '(', '') = ?");
    $stmt->execute([$gsm]);
    $row = $stmt->fetch();

    if ($row) {
        echo json_encode(["status" => "success", "data" => $row], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(["status" => "error", "message" => "No results found"], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }
} else {
    echo json_encode(["status" => "error", "message" => "Invalid request"], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}
?>
