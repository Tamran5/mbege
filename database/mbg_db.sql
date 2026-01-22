-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 22, 2026 at 02:38 AM
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

-- --------------------------------------------------------

--
-- Table structure for table `artikel`
--

CREATE TABLE `artikel` (
  `id` int(11) NOT NULL,
  `judul` varchar(255) NOT NULL,
  `konten` text NOT NULL,
  `foto` varchar(255) DEFAULT NULL,
  `target_role` varchar(20) DEFAULT NULL,
  `dapur_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
-- Table structure for table `log_distribusi`
--

CREATE TABLE `log_distribusi` (
  `id` int(11) NOT NULL,
  `dapur_id` int(11) DEFAULT NULL,
  `sekolah_id` int(11) DEFAULT NULL,
  `foto_bukti` varchar(255) DEFAULT NULL,
  `waktu_sampai` datetime DEFAULT NULL,
  `porsi_sampai` int(11) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL
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
  `vit_b12` float DEFAULT NULL,
  `weight` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
  `total_calcium` float DEFAULT NULL,
  `distribution_date` date NOT NULL,
  `total_iron` float DEFAULT NULL,
  `total_vit_a` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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

-- --------------------------------------------------------

--
-- Table structure for table `ulasan_penerima`
--

CREATE TABLE `ulasan_penerima` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `nama_pengulas` varchar(100) DEFAULT NULL,
  `ulasan_teks` text DEFAULT NULL,
  `tanggal` datetime DEFAULT NULL,
  `rating` int(11) NOT NULL,
  `tags` varchar(255) DEFAULT NULL,
  `status_ai` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
  `otp_created_at` datetime DEFAULT NULL,
  `school_token` varchar(10) DEFAULT NULL,
  `user_class` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password`, `role`, `is_approved`, `fullname`, `nik`, `kitchen_name`, `mitra_type`, `address`, `coordinates`, `file_ktp`, `file_kitchen_photo`, `nisn`, `npsn`, `sekolah_id`, `file_sk_operator`, `school_name`, `student_count`, `province`, `city`, `district`, `village`, `dapur_id`, `phone`, `temp_otp`, `otp_created_at`, `school_token`, `user_class`) VALUES
(1, 'admin_margadana', 'pengawas.margadana@gizi.com', 0x623761643165663534363235393361383863383536353839303339303734646136666431623264333530323235623732616566643461653564653336626565613331666438616132346661633233613337303465383262306465383634376462353034646433633632626439663233616539653832616537386536393464613831323664306662356232386662353864643036336538393666623137653332663437396536336636333961653535326539643830396531613563376539623962, 'super_admin', 1, 'Anton', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, 'Kota Tegal', 'Margadana', NULL, NULL, NULL, NULL, NULL, NULL, NULL);

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
-- Indexes for table `artikel`
--
ALTER TABLE `artikel`
  ADD PRIMARY KEY (`id`),
  ADD KEY `dapur_id` (`dapur_id`);

--
-- Indexes for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `staff_id` (`staff_id`);

--
-- Indexes for table `log_distribusi`
--
ALTER TABLE `log_distribusi`
  ADD PRIMARY KEY (`id`),
  ADD KEY `dapur_id` (`dapur_id`),
  ADD KEY `sekolah_id` (`sekolah_id`);

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
  ADD UNIQUE KEY `school_token` (`school_token`),
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
-- AUTO_INCREMENT for table `artikel`
--
ALTER TABLE `artikel`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `log_distribusi`
--
ALTER TABLE `log_distribusi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `master_ingredients`
--
ALTER TABLE `master_ingredients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `menus`
--
ALTER TABLE `menus`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `menu_ingredients`
--
ALTER TABLE `menu_ingredients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `penerima`
--
ALTER TABLE `penerima`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `staff`
--
ALTER TABLE `staff`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `ulasan_penerima`
--
ALTER TABLE `ulasan_penerima`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `aktivitas_dapur`
--
ALTER TABLE `aktivitas_dapur`
  ADD CONSTRAINT `aktivitas_dapur_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `artikel`
--
ALTER TABLE `artikel`
  ADD CONSTRAINT `artikel_ibfk_1` FOREIGN KEY (`dapur_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  ADD CONSTRAINT `attendance_logs_ibfk_1` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`id`);

--
-- Constraints for table `log_distribusi`
--
ALTER TABLE `log_distribusi`
  ADD CONSTRAINT `log_distribusi_ibfk_1` FOREIGN KEY (`dapur_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `log_distribusi_ibfk_2` FOREIGN KEY (`sekolah_id`) REFERENCES `users` (`id`);

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
