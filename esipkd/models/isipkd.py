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
from   sqlalchemy.orm import relationship  
from ..models import(
      DefaultModel,
      KodeModel,
      NamaModel,
      Base,
      
      )
#####################
#
###########################        
class Pkb(DefaultModel,Base):
    __tablename__ = 'pkbs'
    id = Column(BigInteger, primary_key=True)
    nik = Column(String(16))
    no_rangka = Column(String(16))
    email = Column(String(32))
    mobile_phone = Column(String(16))
    
class Pap(DefaultModel,Base):
    __tablename__ = 'paps'
    id = Column(BigInteger, primary_key=True)
    no_skpd = Column(String(16))
    email = Column(String(32))
    mobile_phone = Column(String(16))
    
class Unit(NamaModel,Base):
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True)
    kode = Column(String(16), unique=True)
    nama = Column(String(128))
    level_id = Column(SmallInteger)
    is_summary = Column(SmallInteger)
    parent_id = Column(SmallInteger)
    
class Rekening(NamaModel,Base):
    __tablename__ = 'rekenings'
    id = Column(Integer, primary_key=True)
    kode = Column(String(24), unique=True)
    nama = Column(String(128))
    level_id = Column(SmallInteger)
    is_summary = Column(SmallInteger)
    parent_id = Column(SmallInteger)

class UnitRekening(Base):
    __tablename__ = 'unit_rekenings'
    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer,ForeignKey("units.id"))
    rekening_id = Column(Integer, ForeignKey("rekenings.id"))
    
class Jabatan(NamaModel, Base):
    __tablename__ = 'jabatans'
    status = Column(Integer, default=1)
    #nama = Column(String(128))
        
class Pegawai(NamaModel, Base):
    __tablename__ = 'pegawais'
    #nama = Column(String(128))
    status = Column(Integer, default=1)
    jabatan_id = Column(Integer,ForeignKey("jabatans.id"))
    unit_id = Column(Integer,ForeignKey("units.id"))
    
class PegawaiLogin(Base):
    __tablename__ = 'pegawai_users'
    user_id    = Column(Integer,ForeignKey("users.id"), primary_key=True)
    pegawai_id = Column(Integer,ForeignKey("pegawais.id"), unique=True)
    change_unit = Column(Integer,default=0, nullable=False)

class Pajak(NamaModel, Base):
    __tablename__ = 'pajaks'
    status = Column(Integer, default=1)
    rekening_id = Column(Integer,ForeignKey("rekenings.id"))
    tahun = Column(Integer, nullable=False, default=0)
    tarif     = Column(Float, default=0, nullable=False)
    UniqueConstraint('rekening_id','tahun', name='rekening_tahun')

class Wilayah(NamaModel,Base):
    __tablename__ = 'wilayahs'
    id = Column(Integer, primary_key=True)
    kode = Column(String(24), unique=True)
    nama = Column(String(128))
    level_id = Column(SmallInteger)
    parent_id = Column(Integer, ForeignKey('wilayahs.id'), nullable=True)
    parent = relationship("Wilayah",
                        backref="child",
                        remote_side=[id])
class SubjekPajak(NamaModel, Base):
    __tablename__ = 'subjekpajaks'
    #nama = Column(String(128))
    status = Column(Integer, default=1)
    alamat_1 = Column(String(128))
    alamat_2 = Column(String(128))

class ObjekPajak(NamaModel, Base):
    __tablename__ = 'objekpajaks'
    status = Column(Integer, default=1)
    alamat_1 = Column(String(128))
    alamat_2 = Column(String(128))
    wilayah_id = Column(Integer, ForeignKey("wilayahs.id"))
    unit_id = Column(Integer,ForeignKey("units.id"))
    pajak_id = Column(Integer, ForeignKey("pajaks.id"))
    subjekpajak_id = Column(Integer, ForeignKey("subjekpajaks.id"))
    
class Sptpd(Base):
    __tablename__ = 'sptpds'
    id = Column(Integer, primary_key=True)
    unit_id     = Column(Integer)
    subjek_pajak_id = Column(Integer, ForeignKey("subjekpajaks.id"))
    objek_pajak_id = Column(Integer, ForeignKey("objekpajaks.id"))
    tahun       = Column(Integer)
    bulan       = Column(Integer)
    nama        = Column(String(64))
    alamat1     = Column(String(128))
    alamat2     = Column(String(128))
    omset       = Column(BigInteger)
    tarif       = Column(Float)
    pokok_pajak = Column(BigInteger)
    denda       = Column(BigInteger)
    jatuh_tempo = Column(Date)
    owner_id    = Column(Integer)
    create_uid  = Column(Integer)
    update_uid  = Column(Integer)
    create_date = Column(DateTime(timezone=True))
    update_date = Column(DateTime(timezone=True))
    status_bayar = Column(SmallInteger)
    
class Sts(Base):
    __tablename__ = 'sts'
    id = Column(Integer, primary_key=True)
    no_bayar    = Column(String(16))
    unit_id     = Column(Integer)
    rekening_id  = Column(Integer)
    pokok_pajak = Column(BigInteger)
    denda       = Column(BigInteger)
    create_uid  = Column(Integer)
    update_uid  = Column(Integer)
    create_date = Column(DateTime(timezone=True))
    update_date = Column(DateTime(timezone=True))
    status_bayar = Column(SmallInteger)
    
class StsItem(Base):
    __tablename__ = 'sts_item'
    sts_id = Column(Integer, primary_key=True)
    sptpd_id = Column(Integer, primary_key=True)
    
class SSPD(Base):
    __tablename__ = 'sspd'
    sts_id = Column(Integer, primary_key=True)
    sptpd_id = Column(Integer, primary_key=True)
    denda = Column(BigInteger)
    bayar = Column(BigInteger)
    tgl_bayar = Column(DateTime)
    tgl_entri = Column(DateTime)
    create_uid  = Column(Integer)
    update_uid  = Column(Integer)
    create_date = Column(DateTime(timezone=True))
    update_date = Column(DateTime(timezone=True))
    
    
class Param(Base):
    __tablename__ = 'params'
    id = Column(Integer, primary_key=True)
    denda       = Column(Integer)
    jatuh_tempo = Column(Integer)

    