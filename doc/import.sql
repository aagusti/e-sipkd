COPY rekenings ( id, kode, uraian, level_id, is_summary) 
    FROM '/home/aagusti/env/esipkd/doc/rekening.csv'
    DELIMITER ',' CSV     HEADER QUOTE '"';
    
    
COPY units ( id, kode, uraian, level_id, is_summary) 
    FROM '/home/aagusti/env/esipkd/doc/unit.csv'
    DELIMITER ',' CSV     HEADER QUOTE '"';
    
    