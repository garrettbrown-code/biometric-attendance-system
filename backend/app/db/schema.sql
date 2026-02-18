PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tbl_class_info (
    fld_ci_code_pk TEXT PRIMARY KEY,      -- class code, lowercase, up to 14 chars
    fld_ci_euid TEXT NOT NULL,            -- professor EUID
    fld_ci_lat REAL NOT NULL,
    fld_ci_lon REAL NOT NULL,
    fld_ci_start_date TEXT NOT NULL,      -- YYYY-MM-DD
    fld_ci_end_date TEXT NOT NULL,        -- YYYY-MM-DD
    CONSTRAINT code_length CHECK(length(fld_ci_code_pk) <= 14),
    CONSTRAINT prof_euid_length CHECK(length(fld_ci_euid) <= 14)
);

CREATE TABLE IF NOT EXISTS tbl_schedule (
    fld_sc_code_fk TEXT NOT NULL,         -- class code
    fld_sc_day TEXT NOT NULL,             -- day of week
    fld_sc_time TEXT NOT NULL,            -- HH:MM:SS
    FOREIGN KEY (fld_sc_code_fk) REFERENCES tbl_class_info(fld_ci_code_pk) ON DELETE CASCADE,
    CONSTRAINT day_format CHECK(
        fld_sc_day IN ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')
    )
);

CREATE TABLE IF NOT EXISTS tbl_sessions (
    fld_se_id_pk INTEGER PRIMARY KEY AUTOINCREMENT,
    fld_se_code_fk TEXT NOT NULL,
    fld_se_date TEXT NOT NULL,            -- YYYY-MM-DD
    fld_se_time TEXT NOT NULL,            -- HH:MM:SS
    FOREIGN KEY (fld_se_code_fk) REFERENCES tbl_class_info(fld_ci_code_pk) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tbl_students (
    fld_st_code_fk TEXT NOT NULL,
    fld_st_euid TEXT NOT NULL,
    PRIMARY KEY (fld_st_code_fk, fld_st_euid),
    FOREIGN KEY (fld_st_code_fk) REFERENCES tbl_class_info(fld_ci_code_pk) ON DELETE CASCADE,
    CONSTRAINT student_euid_length CHECK(length(fld_st_euid) <= 14)
);

CREATE TABLE IF NOT EXISTS tbl_attendance (
    fld_at_id_fk INTEGER NOT NULL,        -- session id
    fld_at_euid_fk TEXT NOT NULL,         -- student euid
    fld_at_attended INTEGER NOT NULL,     -- 1 present, 0 absent
    PRIMARY KEY (fld_at_id_fk, fld_at_euid_fk),
    FOREIGN KEY (fld_at_id_fk) REFERENCES tbl_sessions(fld_se_id_pk) ON DELETE CASCADE,
    CONSTRAINT attendance_bool CHECK(fld_at_attended IN (0, 1))
);

-- Helpful indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_code_date
ON tbl_sessions(fld_se_code_fk, fld_se_date);

CREATE INDEX IF NOT EXISTS idx_class_prof
ON tbl_class_info(fld_ci_euid);

CREATE INDEX IF NOT EXISTS idx_attendance_euid
ON tbl_attendance(fld_at_euid_fk);
