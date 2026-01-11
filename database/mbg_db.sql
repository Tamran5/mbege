-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 11, 2026 at 07:13 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `mbg_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `aktivitas_dapur`
--

CREATE TABLE `aktivitas_dapur` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `jenis_aktivitas` varchar(50) NOT NULL,
  `bukti_foto` varchar(255) NOT NULL,
  `tanggal` date DEFAULT NULL,
  `waktu_mulai` datetime DEFAULT NULL,
  `waktu_selesai` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `catatan` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `alembic_version`
--

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `alembic_version`
--

INSERT INTO `alembic_version` (`version_num`) VALUES
('46537861bdc1');

-- --------------------------------------------------------

--
-- Table structure for table `attendance_logs`
--

CREATE TABLE `attendance_logs` (
  `id` int(11) NOT NULL,
  `staff_id` int(11) NOT NULL,
  `date` date DEFAULT NULL,
  `check_in` datetime DEFAULT NULL,
  `check_out` datetime DEFAULT NULL,
  `status_note` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `master_ingredients`
--

CREATE TABLE `master_ingredients` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `category` varchar(50) DEFAULT NULL,
  `kcal` float DEFAULT 0,
  `carb` float DEFAULT 0,
  `protein` float DEFAULT 0,
  `fat` float DEFAULT 0,
  `fiber` float DEFAULT NULL,
  `calcium` float DEFAULT NULL,
  `iron` float DEFAULT NULL,
  `vit_a` float DEFAULT NULL,
  `vit_c` float DEFAULT NULL,
  `folate` float DEFAULT NULL,
  `vit_b12` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `master_ingredients`
--

INSERT INTO `master_ingredients` (`id`, `user_id`, `name`, `category`, `kcal`, `carb`, `protein`, `fat`, `fiber`, `calcium`, `iron`, `vit_a`, `vit_c`, `folate`, `vit_b12`) VALUES
(4, 6, 'Nasi Putih', 'Karbohidrat', 130, 28, 2.7, 0.3, 0.4, 10, 0.2, 0, 0, 8, 0),
(5, 6, 'Nasi Kuning', 'Karbohidrat', 150, 30, 3, 2.5, 0.5, 15, 0.5, 2, 0, 10, 0),
(6, 6, 'Kentang Rebus', 'Karbohidrat', 87, 20.1, 1.9, 0.1, 1.8, 5, 0.3, 0, 13, 10, 0),
(7, 6, 'Ayam Goreng', 'Protein Hewani', 260, 0, 25, 17, 0, 15, 1.2, 20, 0, 5, 0.4),
(8, 6, 'Ikan Lele Goreng', 'Protein Hewani', 240, 0, 18.5, 14, 0, 20, 1, 10, 0, 10, 1.5),
(9, 6, 'Telur Dadar', 'Protein Hewani', 154, 1, 11, 12, 0, 50, 1.2, 140, 0, 44, 1),
(10, 6, 'Tahu Goreng', 'Protein Nabati', 115, 2.5, 8, 8, 1, 150, 2, 0, 0, 15, 0),
(11, 6, 'Tempe Goreng', 'Protein Nabati', 225, 15, 12, 14, 3, 155, 2.3, 0, 0, 15, 0.1),
(12, 6, 'Sayur Sop', 'Sayuran', 35, 7, 1.5, 0.5, 2, 25, 0.5, 200, 15, 30, 0),
(13, 6, 'Cah Kangkung', 'Sayuran', 45, 5, 2, 2.5, 2, 70, 2, 300, 20, 50, 0),
(14, 6, 'Susu Sapi', 'Buah / Susu', 61, 4.8, 3.2, 3.3, 0, 120, 0.1, 46, 1, 5, 0.4),
(15, 6, 'Pisang Ambon', 'Buah/Susu', 92, 23.4, 1.2, 0.3, 2, 8, 0.4, 15, 10, 20, 0),
(16, 6, 'Nasi Kuning Spesial', 'Karbohidrat', 150, 30, 3, 2.5, 0.5, 15, 0.5, 2, 0, 10, 0),
(17, 8, 'Telur Ayam', 'Protein Nabati', 155, 1.1, 13, 11, 0, 50, 1.2, 520, 0, 44, 1.1),
(18, 8, 'Apel Merah', 'Buah / Susu', 52, 14, 0.3, 0.2, 2.4, 6, 0.1, 54, 4.6, 3, 0),
(19, 8, 'Brokoli Rebus', 'Sayuran', 35, 7, 2.4, 0.4, 3.3, 40, 0.7, 623, 65, 108, 0),
(20, 8, 'Daging Sapi Panggang', 'Protein Hewani', 250, 0, 26, 15, 0, 18, 2.6, 0, 0, 7, 2.6),
(21, 8, 'Roti Gandum', 'Karbohidrat', 247, 41, 13, 3.4, 7, 107, 2.5, 0, 0, 85, 0),
(22, 8, 'Yogurt Plain', 'Buah/Susu', 59, 3.6, 10, 0.4, 0, 110, 0.1, 2, 0, 7, 0.8),
(23, 10, 'Ayam Kampung', 'Protein Hewani', 0, 0, 18, 8, 0, 11, 0, 0, 0, 0, 0);

-- --------------------------------------------------------

--
-- Table structure for table `menus`
--

CREATE TABLE `menus` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `menu_name` varchar(255) NOT NULL,
  `photo` varchar(255) DEFAULT NULL,
  `total_kcal` float DEFAULT 0,
  `total_carb` float DEFAULT 0,
  `total_protein` float DEFAULT 0,
  `total_fat` float DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `total_fiber` float DEFAULT NULL,
  `total_calcium` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `menus`
--

INSERT INTO `menus` (`id`, `user_id`, `menu_name`, `photo`, `total_kcal`, `total_carb`, `total_protein`, `total_fat`, `created_at`, `total_fiber`, `total_calcium`) VALUES
(3, 6, 'Nasi Putih & Ayam Goreng & Tahu Goreng...', 'kunyit.jpg', 601, 42.3, 40.4, 29.1, '2025-12-24 00:15:19', 3.4, 320),
(4, 8, 'Telur Ayam & Brokoli Rebus & Daging Sapi Panggang...', 'kunyit.jpg', 746, 52.7, 64.4, 30.2, '2025-12-24 10:15:09', 10.3, 325);

-- --------------------------------------------------------

--
-- Table structure for table `menu_ingredients`
--

CREATE TABLE `menu_ingredients` (
  `id` int(11) NOT NULL,
  `menu_id` int(11) NOT NULL,
  `ingredient_id` int(11) NOT NULL,
  `weight` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `menu_ingredients`
--

INSERT INTO `menu_ingredients` (`id`, `menu_id`, `ingredient_id`, `weight`) VALUES
(7, 3, 4, 100),
(8, 3, 7, 100),
(9, 3, 10, 100),
(10, 3, 12, 100),
(11, 3, 14, 100),
(12, 4, 21, 100),
(13, 4, 20, 100),
(14, 4, 17, 100),
(15, 4, 19, 100),
(16, 4, 22, 100);

-- --------------------------------------------------------

--
-- Table structure for table `penerima`
--

CREATE TABLE `penerima` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `kategori` varchar(50) NOT NULL,
  `nama_lokasi` varchar(100) NOT NULL,
  `alamat` varchar(200) DEFAULT NULL,
  `kuota` int(11) DEFAULT NULL,
  `pic_nama` varchar(100) DEFAULT NULL,
  `pic_telepon` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `penerima`
--

INSERT INTO `penerima` (`id`, `user_id`, `kategori`, `nama_lokasi`, `alamat`, `kuota`, `pic_nama`, `pic_telepon`) VALUES
(1, 6, 'SD', 'SD N 02 Kidul', 'brebes', 122, 'dani', '099999988');

-- --------------------------------------------------------

--
-- Table structure for table `staff`
--

CREATE TABLE `staff` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `role` varchar(50) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `img_url` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `staff`
--

INSERT INTO `staff` (`id`, `user_id`, `name`, `role`, `phone`, `img_url`, `created_at`) VALUES
(3, 6, 'juni', 'Cook', '9809090', 'https://ui-avatars.com/api/?name=juni&background=11cdef&color=fff', '2025-12-14 18:29:32');

-- --------------------------------------------------------

--
-- Table structure for table `ulasan_penerima`
--

CREATE TABLE `ulasan_penerima` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `nama_pengulas` varchar(100) DEFAULT NULL,
  `ulasan_teks` text NOT NULL,
  `tanggal` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ulasan_penerima`
--

INSERT INTO `ulasan_penerima` (`id`, `user_id`, `nama_pengulas`, `ulasan_teks`, `tanggal`) VALUES
(1, 8, 'Budi Siswa SD 01', 'Makanannya enak banget, ayamnya krispi dan susunya segar!', '2025-12-24 09:45:49'),
(2, 8, 'Siti Aminah', 'Porsinya pas, tapi sayurnya agak sedikit kurang garam.', '2025-12-24 09:45:49'),
(3, 8, 'Agus Pratama', 'Sangat kecewa, nasinya keras dan ayamnya agak dingin.', '2025-12-24 09:45:49'),
(4, 8, 'Rina Septiani', 'Terima kasih makan siangnya, anak-anak sangat suka buah jeruknya.', '2025-12-24 09:45:49'),
(5, 8, 'Dodi Kurniawan', 'Biasa saja, rasanya standar seperti makanan kantin.', '2025-12-24 09:45:49'),
(6, 8, 'Budi Siswa SD', 'Makanannya enak banget, ayamnya krispi dan susunya segar!', '2025-12-24 09:57:32'),
(7, 8, 'Anton B Siswa SD', 'Makanannya enak banget, ayamnya krispi dan susunya segar!', '2025-12-24 09:57:43');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(64) DEFAULT NULL,
  `email` varchar(64) DEFAULT NULL,
  `password` blob DEFAULT NULL,
  `role` varchar(20) DEFAULT NULL,
  `is_approved` tinyint(1) DEFAULT NULL,
  `fullname` varchar(100) DEFAULT NULL,
  `nik` varchar(20) DEFAULT NULL,
  `kitchen_name` varchar(100) DEFAULT NULL,
  `mitra_type` varchar(50) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `coordinates` varchar(100) DEFAULT NULL,
  `file_ktp` varchar(255) DEFAULT NULL,
  `file_kitchen_photo` varchar(255) DEFAULT NULL,
  `nisn` varchar(20) DEFAULT NULL,
  `npsn` varchar(20) DEFAULT NULL,
  `sekolah_id` int(11) DEFAULT NULL,
  `file_sk_operator` varchar(255) DEFAULT NULL,
  `school_name` varchar(100) DEFAULT NULL,
  `student_count` int(11) DEFAULT NULL,
  `province` varchar(100) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `district` varchar(100) DEFAULT NULL,
  `village` varchar(100) DEFAULT NULL,
  `dapur_id` int(11) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `temp_otp` varchar(6) DEFAULT NULL,
  `otp_created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password`, `role`, `is_approved`, `fullname`, `nik`, `kitchen_name`, `mitra_type`, `address`, `coordinates`, `file_ktp`, `file_kitchen_photo`, `nisn`, `npsn`, `sekolah_id`, `file_sk_operator`, `school_name`, `student_count`, `province`, `city`, `district`, `village`, `dapur_id`, `phone`, `temp_otp`, `otp_created_at`) VALUES
(1, 'anton b', 'admin@gmail.com', 0x633465366330356431373035303861343563393832386437363738653365323633626662393738666437313336653836626239326261656161643865623461333832313866653336643830383836623739623066383535373830623663626239613364633531616630393133343738666333623539623738393733333365366236393666303264373238313034313034323533376636306330646362633861323730643138363436363639363034363164376134666665313136313237636334, 'super_admin', 1, '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(2, 'dapur_margadana1', 'marga1@test.com', 0x70617373776f72645f64756d6d79, 'admin_dapur', 1, 'Siti Aminah', '3376010001000001', 'Catering Bunda Siti', 'umkm', 'Jl. Cendrawasih No. 10, Kel. Cabawan', '-6.8898, 109.1122', 'static/assets/img/theme/sketch.jpg', 'static/assets/img/theme/sketch.jpg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(3, 'dapur_margadana2', 'marga2@test.com', 0x70617373776f72645f64756d6d79, 'admin_dapur', 1, 'Budi Santoso', '3376010001000002', 'Dapur Sehat Budi', 'industrial', 'Jl. Abdul Syukur, Kel. Margadana', '-6.8855, 109.1155', 'static/assets/img/theme/sketch.jpg', 'static/assets/img/theme/sketch.jpg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(4, 'dapur_timur1', 'timur1@test.com', 0x70617373776f72645f64756d6d79, 'admin_dapur', 0, 'Agus Setiawan', '3376020001000001', 'Warung Makan Agus', 'umkm', 'Jl. Gajah Mada No. 5', '-6.8688, 109.1400', 'static/assets/img/theme/sketch.jpg', 'static/assets/img/theme/sketch.jpg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(5, 'dapur_selatan1', 'selatan1@test.com', 0x70617373776f72645f64756d6d79, 'admin_dapur', 1, 'Rina Wati', '3376030001000001', 'Rina Bento Kids', 'school', 'Jl. Teuku Umar No. 88', '-6.8900, 109.1200', 'static/assets/img/theme/sketch.jpg', 'static/assets/img/theme/sketch.jpg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(6, 'otong@gmail.com', 'otong@gmail.com', 0x306165356662383537653464343062326632323061616363373961313430363161376263363365323137636337323532653933626331306334616433663439363937613564373939333734383963656462663832323163666537323563646232373139353134373333326531616663303536633161363161396366326330383263353266393336303430316434336466313962373165646132623637316239663739616363623235363764393733373831636166343763336361613135313133, 'admin_dapur', 1, NULL, '1234567890', NULL, 'school', NULL, '-6.8855, 109.1160', '/static/uploads/6e4e2f13_login.png', '/static/uploads/8b167216_login.png', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(7, 'glamy5679@gmail.com', 'glamy5679@gmail.com', 0x386563663261346365393537643166396634343665303839333430383230386262393164633164646235656333646132333332656665626233373462656565353139326264303366333031306538303533383665303838613762313330623834346236633263366434323365326139613630663361323262393933616264323262383434396363326366333166383164653931613562646533333962363836303933306466643039333063613032646163366536356331326338383165396332, 'admin_dapur', 0, 'Nasom 5', '123456790987654', 'mandiri', NULL, 'jl bneaf', '-6.947828, 108.889533', '/static/uploads/bad5228a_kunyit.jpg', '/static/uploads/d1813052_kunyit.jpg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(8, 'muhammadtama171@gmail.com', 'muhammadtama171@gmail.com', 0x396434333938653464313633353265623430656332333532373531616562373930353638666333623838306637666634383435343162306431313062623231613662306162353634366465316339376530633737393165303435316166363239383234613334303764653738333232643630396363373835323431393961653166643663303731326166326232313666383835613832663636663564316539336463663238366561313561363130396463353865396261393131336564323462, 'admin_dapur', 1, 'Muhammad Tama', '12345432134565', 'berkah', NULL, 'Jl.Margadana', '-6.879282, 109.104778', '/static/uploads/f8e9cdce_kunyit.jpg', '/static/uploads/14ab61a8_kunyit.jpg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(9, 'admin gizi', 'admin.tegal@gizi.com', 0x393035376164323731303238306334323437373432393837373661613437356539356430363964393733316639353932633837333538613933393166376635363038313235333965623264373837386265356330356466306634616136656232323830393164633631616333316137623731326363626166626536383662623635623435336232383464663165366133633438346130656564623363336666383562306139343639613438653438623036353138323361336338623331323335, 'super_admin', 1, 'Admin Gizi Kota Tegal', NULL, NULL, NULL, 'Kantor Dinas Gizi Margadana, Kota Tegal', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 'JAWA TENGAH', 'KOTA TEGAL', 'MARGADANA', 'MARGADANA', NULL, NULL, NULL, NULL),
(10, 'yanto@gmail.com', 'yanto@gmail.com', 0x333963633837376666373166336337636632393637366361373266366365616564386266616633643731383138653237633838646431353136636238623031643261343966653063613134353932613461386563356165663232326630643364343139623461366535653330666230373165343133313235653565636164383364353636376338653531353535333232313438623730326236343439636231383064333037373531373433333438616630613335336263303338613433623364, 'admin_dapur', 1, 'yanto', '123456789', 'Dapur Sehat Sentausa', NULL, 'Jalan Margadana 1', '-7.739967, 110.664568', '/static/uploads/19afdc1a_jarkom.jpg', '/static/uploads/278ceae6_jarkom.jpg', NULL, NULL, NULL, NULL, NULL, 0, 'JAWA TENGAH', NULL, 'MARGADANA', NULL, NULL, NULL, NULL, NULL),
(13, '09737467', 'upbeat.marco@gmail.com', 0x616133306535623961383433363930656663346264303634366532316537353337323366353831373631613532666137333135396338353835373137316263346136363233383164653339383863623738653962386464353636393330343031356262336430666666616131646334386237616365343362623330346466383336396335366463366232363837396630376265666334386639363364616639323163626433303562316661356234653139343734373237616566656664643361, 'pengelola_sekolah', 1, 'budiman', NULL, NULL, NULL, 'Jalan Jendral Otong', NULL, NULL, NULL, NULL, '6655780', NULL, 'documents/sk\\20260104233343_scaled_kunyit.jpg', 'SDN 09 Jonggol', 200, 'JAWA TENGAH', 'KOTA TEGAL', 'MARGADANA', 'Jalan Margadana', 10, '0876454675', NULL, '2026-01-06 13:59:18'),
(14, NULL, 'santoso@gmail.com', 0x633339646433343462306231326636316430333835333139326634383165306531333866326631373636326238353538663733393430616135326432313933376638666365353033383237383562386533666663336465656636653036343439643432313033336263333839316563646632316362633530633665326162616232666466653935343864373233363633306533386561356237633935346430373662653266343838643536633837333764363362643862393730313762623161, 'pengelola_sekolah', 0, 'Budi Santoso', NULL, NULL, NULL, 'Jalan Margadana Sudibyo', NULL, NULL, NULL, NULL, '439056', NULL, 'documents/sk/20260105182836_scaled_kunyit.jpg', 'SMA N 07 Margadana', 400, 'JAWA TENGAH', 'KOTA TEGAL', 'MARGADANA', 'Margadana Kidul', 10, '087854903678', NULL, NULL),
(15, NULL, 'andi@gmail.com', 0x316464396231636332333161663064663461613331393162333562646130333236656363366139653737306231386437353061626630316131356165623166613033613031386439663538313130646130313065396236633966643361343736366430646565356432373634633265363837656261336665353638613563396463383866353034323539636438353134316337356566336164353134643431333331653639306235326166313033643234396362666333663830356237366139, 'pengelola_sekolah', 0, 'Andi', NULL, NULL, NULL, 'Jalan Sudibyo', NULL, NULL, NULL, NULL, '78656', NULL, 'documents/sk/20260105202001_scaled_kunyit.jpg', 'SMP N 08 Tegal', 500, 'JAWA TENGAH', 'KOTA TEGAL', 'MARGADANA', 'Margadana Wetan', 10, '0876767678', NULL, NULL),
(16, NULL, 'untung@gmail.com', 0x356135396264316438323930363564653039396266313331333837623634363137303932356630306533363538353734356436626239376431373238393265393038326331653532306536313766376664333939343665396461363363376162396435353330373131343238393164323031626161616165313765313262663561386334353164333139356266396363313036623134633165396539633535663135306233363839373733393239343865643434396366366335623038323336, 'lansia', 1, 'Untung supratman', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 'JAWA TENGAH', 'KOTA TEGAL', 'MARGADANA', 'marganada selatan', 10, '0896755457', NULL, NULL),
(17, NULL, 'surotong@gmail.com', 0x626636383966356636366362363935306662336139663031633830373565613738643934353562396565623938323336306636396465623564306532623539373462343764356235356661626135353133336562323266653261613438363733356563666463346635346635363431613961343162333562633465383666303438636437343030366161346139653739636565396635323233313632373262326338633064386239366135376631616331373064373562663938393939353165, 'admin_dapur', 1, 'otong', '878678687687', 'Jaya Sentausa', NULL, 'Margadana barat', '-6.947817, 108.889536', '/static/uploads/a817f4e0_kunyit.jpg', '/static/uploads/dfb5d925_kunyit.jpg', NULL, NULL, NULL, NULL, NULL, 0, 'JAWA TENGAH', NULL, 'MARGADANA', NULL, NULL, NULL, NULL, NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `aktivitas_dapur`
--
ALTER TABLE `aktivitas_dapur`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`);

--
-- Indexes for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `staff_id` (`staff_id`);

--
-- Indexes for table `master_ingredients`
--
ALTER TABLE `master_ingredients`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `menus`
--
ALTER TABLE `menus`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `menu_ingredients`
--
ALTER TABLE `menu_ingredients`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_ingredient` (`ingredient_id`),
  ADD KEY `menu_id` (`menu_id`);

--
-- Indexes for table `penerima`
--
ALTER TABLE `penerima`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `staff`
--
ALTER TABLE `staff`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `ulasan_penerima`
--
ALTER TABLE `ulasan_penerima`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `sekolah_id` (`sekolah_id`),
  ADD KEY `dapur_id` (`dapur_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `aktivitas_dapur`
--
ALTER TABLE `aktivitas_dapur`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `master_ingredients`
--
ALTER TABLE `master_ingredients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `menus`
--
ALTER TABLE `menus`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `menu_ingredients`
--
ALTER TABLE `menu_ingredients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT for table `penerima`
--
ALTER TABLE `penerima`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `staff`
--
ALTER TABLE `staff`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `ulasan_penerima`
--
ALTER TABLE `ulasan_penerima`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `aktivitas_dapur`
--
ALTER TABLE `aktivitas_dapur`
  ADD CONSTRAINT `aktivitas_dapur_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  ADD CONSTRAINT `attendance_logs_ibfk_1` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`id`);

--
-- Constraints for table `master_ingredients`
--
ALTER TABLE `master_ingredients`
  ADD CONSTRAINT `master_ingredients_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `menus`
--
ALTER TABLE `menus`
  ADD CONSTRAINT `menus_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `menu_ingredients`
--
ALTER TABLE `menu_ingredients`
  ADD CONSTRAINT `fk_ingredient` FOREIGN KEY (`ingredient_id`) REFERENCES `master_ingredients` (`id`),
  ADD CONSTRAINT `menu_ingredients_ibfk_1` FOREIGN KEY (`menu_id`) REFERENCES `menus` (`id`);

--
-- Constraints for table `penerima`
--
ALTER TABLE `penerima`
  ADD CONSTRAINT `penerima_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `staff`
--
ALTER TABLE `staff`
  ADD CONSTRAINT `staff_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `ulasan_penerima`
--
ALTER TABLE `ulasan_penerima`
  ADD CONSTRAINT `ulasan_penerima_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`sekolah_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `users_ibfk_2` FOREIGN KEY (`dapur_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
