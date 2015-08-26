from sqlalchemy import (
    Column,
    Index,
    Integer,
    SmallInteger,
    Text,
    BigInteger,
    String,
    Float,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint
    )
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound
import transaction
from ..models import(
      DBSession,
      DefaultModel,
      KodeModel,
      NamaModel,
      Base,
      User,
      CommonModel
      )
      
    #######################
    ##   Model E-SIPKD   ## 
    #######################        
class Pkb(DefaultModel,Base):
    __tablename__ = 'pkbs'
    id              = Column(BigInteger,   primary_key=True)
    kd_status       = Column(SmallInteger, default=0)
    flag_sms        = Column(SmallInteger, default=0)    
    no_ktp          = Column(String(16)) 
    no_rangka       = Column(String(40))   
    email           = Column(String(40))   
    no_hp           = Column(String(20))   
    tg_pros_daftar  = Column(Date)
    jam_daftar      = Column(String(10))   
    ket             = Column(String(40))   
    kd_bayar        = Column(String(16))   
    kd_wil          = Column(String(2)) 
    kd_wil_proses   = Column(String(2))  
    nm_pemilik      = Column(String(40))   
    no_polisi       = Column(String(10))   
    warna_tnkb      = Column(String(40))   
    milik_ke        = Column(Integer)
    nm_merek_kb     = Column(String(40))   
    nm_model_kb     = Column(String(40))   
    th_buatan       = Column(String(4))  
    tg_akhir_pjklm  = Column(Date)
    tg_akhir_pjkbr  = Column(Date)
    bbn_pok         = Column(BigInteger, default=0)   
    bbn_den         = Column(BigInteger, default=0)   
    pkb_pok         = Column(BigInteger, default=0)   
    pkb_den         = Column(BigInteger, default=0)  
    swd_pok         = Column(BigInteger, default=0)   
    swd_den         = Column(BigInteger, default=0)   
    adm_stnk        = Column(BigInteger, default=0)  
    adm_tnkb        = Column(BigInteger, default=0)   
    jumlah          = Column(BigInteger, default=0)   
    tg_bayar_bank   = Column(Date)
    jam_bayar_bank  = Column(String(10))   
    kd_trn_bank     = Column(String(20))   
    kd_trn_dpd      = Column(String(20))   
    ivr             = Column(String(2))
    
class Pap(DefaultModel,Base):
    __tablename__ = 'paps'
    id            = Column(BigInteger,   primary_key=True)
    kd_status     = Column(SmallInteger, default=0) 
    kd_bayar      = Column(String(16))
    npwpd         = Column(String(14))
    nm_perus      = Column(String(40))
    al_perus      = Column(String(50))
    vol_air       = Column(BigInteger, default=0)
    npa           = Column(BigInteger, default=0)  
    bea_pok_pjk   = Column(BigInteger, default=0)  
    bea_den_pjk   = Column(BigInteger, default=0)  
    m_pjk_bln     = Column(String(2))
    m_pjk_thn     = Column(String(4))
    tgl_tetap     = Column(Date)  
    tgl_jt_tempo  = Column(Date)    
    keterangan    = Column(String(255))
    
class Unit(NamaModel,Base):
    __tablename__ = 'units'
    id            = Column(Integer,    primary_key=True)
    kode          = Column(String(16), unique=True)
    nama          = Column(String(128))
    level_id      = Column(SmallInteger)
    is_summary    = Column(SmallInteger)
    parent_id     = Column(SmallInteger)
 
class UserUnit(Base):
    __tablename__  = 'user_units'
     
    units    = relationship("Unit", backref=backref('user_units'))
    users    = relationship("User", backref=backref('user_units'))                  
    user_id  = Column(Integer, ForeignKey('users.id'), primary_key=True)
    unit_id  = Column(Integer, ForeignKey('units.id'), primary_key=True)
    
    @classmethod
    def get_by_email(cls, email):
        user = User.get_by_email(email)
        return cls.get_by_user(user)
        
    @classmethod
    def _get_by_user(cls, user):
        return DBSession.query(cls).filter_by(user_id=user.id).all()
        
    @classmethod
    def get_by_user(cls, user):
        units = []
        for g in cls._get_by_user(user):
            units.append(g.unit_id)
        return units
                
    @classmethod
    def set_one(cls, session, user, unit):
        member = DBSession.query(cls).filter_by(user_id=user.id, unit_id=unit.id)
        try:
            member = member.one()
        except NoResultFound:
            member = cls(user_id=user.id, unit_id=unit.id)
            DBSession.add(member)
            transaction.commit()
        
    @classmethod
    def set_all(cls, user, unit_ids=[]):
        if type(user) in [StringType, UnicodeType]:
            user = User.get_by_email(user)
        olds = cls._get_by_user(user)
        news = []
        for unit_id in unit_ids:
            unit = DBSession.query(Unit).get(unit_id)
            member = cls.set_one(user, unit)
            news.append(unit)
        for old in olds:
            if old not in news:
                old.delete()
                DBSession.commit()
                
    @classmethod
    def get_by_unit(cls, unit):
        users = []
        for g in DBSession.query(cls).filter_by(unit=unit):
            users.append(g.user)
        return users    
         
class Rekening(NamaModel,Base):
    __tablename__ = 'rekenings'
    id            = Column(Integer,    primary_key=True)
    kode          = Column(String(24), unique=True)
    nama          = Column(String(128))
    level_id      = Column(SmallInteger)
    is_summary    = Column(SmallInteger)
    parent_id     = Column(SmallInteger)

class UnitRekening(Base):
    __tablename__ = 'unit_rekenings'
    id            = Column(Integer, primary_key=True)
    unit_id       = Column(Integer, ForeignKey("units.id"))
    rekening_id   = Column(Integer, ForeignKey("rekenings.id"))
    
class Jabatan(NamaModel, Base):
    __tablename__ = 'jabatans'
    status        = Column(Integer, default=1)
    UniqueConstraint('kode')    
    #nama = Column(String(128))
        
class Pegawai(NamaModel, Base):
    __tablename__ = 'pegawais'
    #nama        = Column(String(128))
    status        = Column(Integer, default=1)
    jabatan_id    = Column(Integer, ForeignKey("jabatans.id"))
    unit_id       = Column(Integer, ForeignKey("units.id"))
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    users         = relationship("User", backref=backref('pegawais'))

    UniqueConstraint('kode')    
    
    @classmethod
    def get_by_user(cls, user_id):
        return DBSession.query(cls).filter(cls.user_id==user_id).all()
    
class PegawaiLogin(Base):
    __tablename__ = 'pegawai_users'
    user_id       = Column(Integer, ForeignKey("users.id"),    primary_key=True)
    pegawai_id    = Column(Integer, ForeignKey("pegawais.id"), unique=True)
    change_unit   = Column(Integer, default=0, nullable=False)

class Pajak(NamaModel, Base):
    __tablename__     = 'pajaks'
    status            = Column(Integer, default=1)
    rekening_id       = Column(Integer, ForeignKey("rekenings.id"))
    tahun             = Column(Integer, nullable=False, default=0)
    tarif             = Column(Float,   nullable=False, default=0)
    denda_rekening_id = Column(Integer, nullable=True,  default=0)

    UniqueConstraint('rekening_id','tahun', name='rekening_tahun')
    rekenings         = relationship("Rekening", backref=backref('pajaks'))

class Wilayah(NamaModel,Base):
    __tablename__ = 'wilayahs'
    id            = Column(Integer,    primary_key=True)
    kode          = Column(String(24), unique=True)
    nama          = Column(String(128))
    level_id      = Column(SmallInteger)
    parent_id     = Column(Integer, ForeignKey('wilayahs.id'), nullable=True)
    parent        = relationship("Wilayah",
                               backref="child",
                               remote_side=[id])
                        
class SubjekPajak(NamaModel, Base):
    __tablename__ = 'subjekpajaks'
    status        = Column(Integer, default=1)
    alamat_1      = Column(String(128))
    alamat_2      = Column(String(128))
    kelurahan     = Column(String(128))
    kecamatan     = Column(String(128))
    kota          = Column(String(128))
    user_id       = Column(Integer, ForeignKey("users.id"))
    provinsi      = Column(String(128))
    email         = Column(String(40))   
    unit_id       = Column(Integer, ForeignKey("units.id"))
    users         = relationship("User", backref=backref('subjekpajaks'))
    units         = relationship('Unit', backref=backref('subjekpajaks'))
    
    UniqueConstraint('kode')
    
    # get_by_user untuk wp non global
    @classmethod
    def get_by_user_wp(cls, user_id):
        return DBSession.query(cls).filter_by(user_id=user_id).first()
        
    # get_by_user untuk wp global
    @classmethod
    def get_by_user(cls, user_id):
        return DBSession.query(cls).filter_by(user_id=user_id).all()
     
class ObjekPajak(NamaModel, Base):
    __tablename__  = 'objekpajaks'
    __table_args__ = (UniqueConstraint('subjekpajak_id', 'kode', 
                                       name='objekpajak_kode_uq'),)
    status         = Column(Integer, default=1)
    alamat_1       = Column(String(128))
    alamat_2       = Column(String(128))
    wilayah_id     = Column(Integer, ForeignKey("wilayahs.id"))
    unit_id        = Column(Integer, ForeignKey("units.id"))
    pajak_id       = Column(Integer, ForeignKey("pajaks.id"))
    subjekpajak_id = Column(Integer, ForeignKey("subjekpajaks.id")) 
    subjekpajaks   = relationship('SubjekPajak', backref=backref('objekpajaks'))
    pajaks         = relationship('Pajak',       backref=backref('objekpajaks'))
    wilayahs       = relationship('Wilayah',     backref=backref('objekpajaks'))
    units          = relationship('Unit',        backref=backref('objekpajaks'))
    
class ARInvoice(CommonModel, Base):
    __tablename__   = 'arinvoices'
    id              = Column(Integer, primary_key=True)
    tahun_id        = Column(Integer)
    unit_id         = Column(Integer, ForeignKey("units.id"))
    no_id           = Column(Integer)
    subjek_pajak_id = Column(Integer, ForeignKey("subjekpajaks.id"))
    objek_pajak_id  = Column(Integer, ForeignKey("objekpajaks.id"))
    kode            = Column(String(32), unique=True)
    unit_kode       = Column(String(32))
    unit_nama       = Column(String(128))
    rekening_id     = Column(Integer, ForeignKey("rekenings.id"))
    rek_kode        = Column(String(16))    
    rek_nama        = Column(String(64))   
    wp_kode         = Column(String(16))
    wp_nama         = Column(String(64))
    wp_alamat_1     = Column(String(128))
    wp_alamat_2     = Column(String(128))
    op_kode         = Column(String(16))
    op_nama         = Column(String(64))
    op_alamat_1     = Column(String(128))
    op_alamat_2     = Column(String(128))
    dasar           = Column(BigInteger)
    tarif           = Column(Float)
    pokok           = Column(BigInteger)
    denda           = Column(BigInteger)
    bunga           = Column(BigInteger)
    jumlah          = Column(BigInteger)
    periode_1       = Column(Date)
    periode_2       = Column(Date)
    tgl_tetap       = Column(Date)
    jatuh_tempo     = Column(Date)
    status_bayar    = Column(SmallInteger, nullable=False, default=0) # 0 belum bayar 1 sudah bayar 2 batal
    owner_id        = Column(Integer)
    create_uid      = Column(Integer)
    update_uid      = Column(Integer)
    create_date     = Column(DateTime(timezone=True))
    update_date     = Column(DateTime(timezone=True))
    status_grid     = Column(SmallInteger, nullable=False, default=0) # 0 Register 1 Pembayaran_cepat
    wilayah_id      = Column(Integer, ForeignKey("wilayahs.id"))
	
    subjekpajaks    = relationship("SubjekPajak", backref=backref('arinvoices'))
    objekpajaks     = relationship("ObjekPajak",  backref=backref('arinvoices'))
    wilayahs        = relationship("Wilayah",     backref=backref('arinvoices'))
    units           = relationship("Unit",        backref=backref('arinvoices'))
    UniqueConstraint(tahun_id,unit_id,no_id,name='arinvoice_uq')
    
class ARSspd(CommonModel, Base):
    __tablename__ = 'arsspds'
    id            = Column(Integer, primary_key=True)
    tahun_id      = Column(Integer)
    unit_id       = Column(Integer, ForeignKey("units.id"))
    arinvoice_id  = Column(Integer, ForeignKey("arinvoices.id"))
    pembayaran_ke = Column(Integer)
    bunga         = Column(BigInteger)
    bayar         = Column(BigInteger)
    tgl_bayar     = Column(DateTime)
    create_uid    = Column(Integer)
    update_uid    = Column(Integer)
    create_date   = Column(DateTime(timezone=True))
    update_date   = Column(DateTime(timezone=True))
    posted        = Column(SmallInteger, nullable=False, default=0)
    ntb           = Column(String(20))   
    ntp           = Column(String(20))
    bank_id       = Column(Integer)
    channel_id    = Column(Integer)
    arinvoices    = relationship("ARInvoice", backref=backref('arsspds'))
    units         = relationship("Unit",      backref=backref('arsspds'))
    UniqueConstraint(arinvoice_id,pembayaran_ke,name='arsspd_uq')
    UniqueConstraint(tahun_id,unit_id,name='arsspd_no_uq')
                        
class ARSts(NamaModel,Base):
    __tablename__ = 'arsts'
    tahun_id      = Column(Integer)
    unit_id       = Column(Integer, ForeignKey("units.id"))
    tgl_sts       = Column(DateTime(timezone=True))
    unit_kode     = Column(String(32))
    unit_nama     = Column(String(128))
    no_id         = Column(Integer)
    virified      = Column(SmallInteger, nullable=False, default=0)
    posted        = Column(SmallInteger, nullable=False, default=0)
    create_uid    = Column(Integer)
    update_uid    = Column(Integer)
    create_date   = Column(DateTime(timezone=True))
    update_date   = Column(DateTime(timezone=True))
    status_bayar  = Column(SmallInteger)
    jumlah        = Column(BigInteger, nullable=False, default=0)
    units         = relationship("Unit", backref=backref('arsts'))
    UniqueConstraint(tahun_id,unit_id,no_id,name='arsts_no_uq')
    
class ARStsItem(Base):
    __tablename__ = 'arsts_item'
    sts_id        = Column(Integer, primary_key=True)
    sspd_id       = Column(Integer, ForeignKey('arsspds.id'),   primary_key=True)
    rekening_id   = Column(Integer, ForeignKey('rekenings.id'), primary_key=True)
    jumlah        = Column(BigInteger, nullable=False, default=0)
    sspds         = relationship("ARSspd",   backref=backref('arstsitems'))
    rekenings     = relationship("Rekening", backref=backref('arstsitems'))
    
class Param(Base):
    __tablename__ = 'params'
    id            = Column(Integer, primary_key=True)
    denda         = Column(Integer)
    jatuh_tempo   = Column(Integer)

    