PRAGMA page_size=4096;
-- PRAGMA encoding='UTF-8';
-- PRAGMA auto_vacuum=NONE;
-- PRAGMA max_page_count=1073741823;

BEGIN TRANSACTION;

-- Table  addresses
DROP TABLE IF EXISTS addresses;
CREATE TABLE addresses(
                      address TEXT UNIQUE,
                      options INTEGER,
                      block_index INTEGER);
-- Triggers and indices on  addresses
CREATE TRIGGER _addresses_delete BEFORE DELETE ON addresses BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO addresses(rowid,address,options,block_index) VALUES('||old.rowid||','||quote(old.address)||','||quote(old.options)||','||quote(old.block_index)||')');
                            END;
CREATE TRIGGER _addresses_insert AFTER INSERT ON addresses BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM addresses WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _addresses_update AFTER UPDATE ON addresses BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE addresses SET address='||quote(old.address)||',options='||quote(old.options)||',block_index='||quote(old.block_index)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX addresses_idx ON addresses (address);

-- Table  assets
DROP TABLE IF EXISTS assets;
CREATE TABLE assets(
                      asset_id TEXT UNIQUE,
                      asset_name TEXT UNIQUE,
                      block_index INTEGER,
                      asset_longname TEXT);
INSERT INTO assets VALUES('0','BTC',NULL,NULL);
INSERT INTO assets VALUES('1','XCP',NULL,NULL);
INSERT INTO assets VALUES('18279','BBBB',310005,NULL);
INSERT INTO assets VALUES('18280','BBBC',310006,NULL);
-- Triggers and indices on  assets
CREATE TRIGGER _assets_delete BEFORE DELETE ON assets BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO assets(rowid,asset_id,asset_name,block_index,asset_longname) VALUES('||old.rowid||','||quote(old.asset_id)||','||quote(old.asset_name)||','||quote(old.block_index)||','||quote(old.asset_longname)||')');
                            END;
CREATE TRIGGER _assets_insert AFTER INSERT ON assets BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM assets WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _assets_update AFTER UPDATE ON assets BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE assets SET asset_id='||quote(old.asset_id)||',asset_name='||quote(old.asset_name)||',block_index='||quote(old.block_index)||',asset_longname='||quote(old.asset_longname)||' WHERE rowid='||old.rowid);
                            END;
CREATE UNIQUE INDEX asset_longname_idx ON assets(asset_longname);
CREATE INDEX id_idx ON assets (asset_id);
CREATE INDEX name_idx ON assets (asset_name);

-- Table  balances
DROP TABLE IF EXISTS balances;
CREATE TABLE balances(
                      address TEXT,
                      asset TEXT,
                      quantity INTEGER);
INSERT INTO balances VALUES('mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',149849426438);
INSERT INTO balances VALUES('mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','XCP',50420824);
INSERT INTO balances VALUES('mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBB',996000000);
INSERT INTO balances VALUES('mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBC',89474);
INSERT INTO balances VALUES('mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','BBBB',4000000);
INSERT INTO balances VALUES('mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','BBBC',10526);
-- Triggers and indices on  balances
CREATE TRIGGER _balances_delete BEFORE DELETE ON balances BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO balances(rowid,address,asset,quantity) VALUES('||old.rowid||','||quote(old.address)||','||quote(old.asset)||','||quote(old.quantity)||')');
                            END;
CREATE TRIGGER _balances_insert AFTER INSERT ON balances BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM balances WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _balances_update AFTER UPDATE ON balances BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE balances SET address='||quote(old.address)||',asset='||quote(old.asset)||',quantity='||quote(old.quantity)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX address_asset_idx ON balances (address, asset);

-- Table  bet_expirations
DROP TABLE IF EXISTS bet_expirations;
CREATE TABLE bet_expirations(
                      bet_index INTEGER PRIMARY KEY,
                      bet_hash TEXT UNIQUE,
                      source TEXT,
                      block_index INTEGER,
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index),
                      FOREIGN KEY (bet_index, bet_hash) REFERENCES bets(tx_index, tx_hash));
INSERT INTO bet_expirations VALUES(13,'7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',310023);
-- Triggers and indices on  bet_expirations
CREATE TRIGGER _bet_expirations_delete BEFORE DELETE ON bet_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO bet_expirations(rowid,bet_index,bet_hash,source,block_index) VALUES('||old.rowid||','||quote(old.bet_index)||','||quote(old.bet_hash)||','||quote(old.source)||','||quote(old.block_index)||')');
                            END;
CREATE TRIGGER _bet_expirations_insert AFTER INSERT ON bet_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM bet_expirations WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _bet_expirations_update AFTER UPDATE ON bet_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE bet_expirations SET bet_index='||quote(old.bet_index)||',bet_hash='||quote(old.bet_hash)||',source='||quote(old.source)||',block_index='||quote(old.block_index)||' WHERE rowid='||old.rowid);
                            END;

-- Table  bet_match_expirations
DROP TABLE IF EXISTS bet_match_expirations;
CREATE TABLE bet_match_expirations(
                      bet_match_id TEXT PRIMARY KEY,
                      tx0_address TEXT,
                      tx1_address TEXT,
                      block_index INTEGER,
                      FOREIGN KEY (bet_match_id) REFERENCES bet_matches(id),
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index));
-- Triggers and indices on  bet_match_expirations
CREATE TRIGGER _bet_match_expirations_delete BEFORE DELETE ON bet_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO bet_match_expirations(rowid,bet_match_id,tx0_address,tx1_address,block_index) VALUES('||old.rowid||','||quote(old.bet_match_id)||','||quote(old.tx0_address)||','||quote(old.tx1_address)||','||quote(old.block_index)||')');
                            END;
CREATE TRIGGER _bet_match_expirations_insert AFTER INSERT ON bet_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM bet_match_expirations WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _bet_match_expirations_update AFTER UPDATE ON bet_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE bet_match_expirations SET bet_match_id='||quote(old.bet_match_id)||',tx0_address='||quote(old.tx0_address)||',tx1_address='||quote(old.tx1_address)||',block_index='||quote(old.block_index)||' WHERE rowid='||old.rowid);
                            END;

-- Table  bet_match_resolutions
DROP TABLE IF EXISTS bet_match_resolutions;
CREATE TABLE bet_match_resolutions(
                      bet_match_id TEXT PRIMARY KEY,
                      bet_match_type_id INTEGER,
                      block_index INTEGER,
                      winner TEXT,
                      settled BOOL,
                      bull_credit INTEGER,
                      bear_credit INTEGER,
                      escrow_less_fee INTEGER,
                      fee INTEGER,
                      FOREIGN KEY (bet_match_id) REFERENCES bet_matches(id),
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index));
INSERT INTO bet_match_resolutions VALUES('7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81_e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42',1,310018,'0',0,59137500,NULL,NULL,3112500);
INSERT INTO bet_match_resolutions VALUES('3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a_a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8',1,310019,'1',159300000,315700000,NULL,NULL,25000000);
INSERT INTO bet_match_resolutions VALUES('194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5_72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207',5,310020,NULL,NULL,NULL,'NotEqual',1330000000,70000000);
-- Triggers and indices on  bet_match_resolutions
CREATE TRIGGER _bet_match_resolutions_delete BEFORE DELETE ON bet_match_resolutions BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO bet_match_resolutions(rowid,bet_match_id,bet_match_type_id,block_index,winner,settled,bull_credit,bear_credit,escrow_less_fee,fee) VALUES('||old.rowid||','||quote(old.bet_match_id)||','||quote(old.bet_match_type_id)||','||quote(old.block_index)||','||quote(old.winner)||','||quote(old.settled)||','||quote(old.bull_credit)||','||quote(old.bear_credit)||','||quote(old.escrow_less_fee)||','||quote(old.fee)||')');
                            END;
CREATE TRIGGER _bet_match_resolutions_insert AFTER INSERT ON bet_match_resolutions BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM bet_match_resolutions WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _bet_match_resolutions_update AFTER UPDATE ON bet_match_resolutions BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE bet_match_resolutions SET bet_match_id='||quote(old.bet_match_id)||',bet_match_type_id='||quote(old.bet_match_type_id)||',block_index='||quote(old.block_index)||',winner='||quote(old.winner)||',settled='||quote(old.settled)||',bull_credit='||quote(old.bull_credit)||',bear_credit='||quote(old.bear_credit)||',escrow_less_fee='||quote(old.escrow_less_fee)||',fee='||quote(old.fee)||' WHERE rowid='||old.rowid);
                            END;

-- Table  bet_matches
DROP TABLE IF EXISTS bet_matches;
CREATE TABLE bet_matches(
                      id TEXT PRIMARY KEY,
                      tx0_index INTEGER,
                      tx0_hash TEXT,
                      tx0_address TEXT,
                      tx1_index INTEGER,
                      tx1_hash TEXT,
                      tx1_address TEXT,
                      tx0_bet_type INTEGER,
                      tx1_bet_type INTEGER,
                      feed_address TEXT,
                      initial_value INTEGER,
                      deadline INTEGER,
                      target_value REAL,
                      leverage INTEGER,
                      forward_quantity INTEGER,
                      backward_quantity INTEGER,
                      tx0_block_index INTEGER,
                      tx1_block_index INTEGER,
                      block_index INTEGER,
                      tx0_expiration INTEGER,
                      tx1_expiration INTEGER,
                      match_expire_index INTEGER,
                      fee_fraction_int INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx0_index, tx0_hash, tx0_block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                      FOREIGN KEY (tx1_index, tx1_hash, tx1_block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
INSERT INTO bet_matches VALUES('7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81_e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42',13,'7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',14,'e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',0,1,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',100,1388000100,0.0,15120,41500000,20750000,310012,310013,310013,10,10,310022,99999999,'settled: liquidated for bear');
INSERT INTO bet_matches VALUES('3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a_a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8',15,'3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',16,'a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',0,1,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',100,1388000100,0.0,5040,150000000,350000000,310014,310015,310015,10,10,310024,99999999,'settled');
INSERT INTO bet_matches VALUES('194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5_72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207',17,'194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',18,'72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',2,3,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',100,1388000200,1.0,5040,750000000,650000000,310016,310017,310017,10,10,310026,99999999,'settled: for notequal');
-- Triggers and indices on  bet_matches
CREATE TRIGGER _bet_matches_delete BEFORE DELETE ON bet_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO bet_matches(rowid,id,tx0_index,tx0_hash,tx0_address,tx1_index,tx1_hash,tx1_address,tx0_bet_type,tx1_bet_type,feed_address,initial_value,deadline,target_value,leverage,forward_quantity,backward_quantity,tx0_block_index,tx1_block_index,block_index,tx0_expiration,tx1_expiration,match_expire_index,fee_fraction_int,status) VALUES('||old.rowid||','||quote(old.id)||','||quote(old.tx0_index)||','||quote(old.tx0_hash)||','||quote(old.tx0_address)||','||quote(old.tx1_index)||','||quote(old.tx1_hash)||','||quote(old.tx1_address)||','||quote(old.tx0_bet_type)||','||quote(old.tx1_bet_type)||','||quote(old.feed_address)||','||quote(old.initial_value)||','||quote(old.deadline)||','||quote(old.target_value)||','||quote(old.leverage)||','||quote(old.forward_quantity)||','||quote(old.backward_quantity)||','||quote(old.tx0_block_index)||','||quote(old.tx1_block_index)||','||quote(old.block_index)||','||quote(old.tx0_expiration)||','||quote(old.tx1_expiration)||','||quote(old.match_expire_index)||','||quote(old.fee_fraction_int)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _bet_matches_insert AFTER INSERT ON bet_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM bet_matches WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _bet_matches_update AFTER UPDATE ON bet_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE bet_matches SET id='||quote(old.id)||',tx0_index='||quote(old.tx0_index)||',tx0_hash='||quote(old.tx0_hash)||',tx0_address='||quote(old.tx0_address)||',tx1_index='||quote(old.tx1_index)||',tx1_hash='||quote(old.tx1_hash)||',tx1_address='||quote(old.tx1_address)||',tx0_bet_type='||quote(old.tx0_bet_type)||',tx1_bet_type='||quote(old.tx1_bet_type)||',feed_address='||quote(old.feed_address)||',initial_value='||quote(old.initial_value)||',deadline='||quote(old.deadline)||',target_value='||quote(old.target_value)||',leverage='||quote(old.leverage)||',forward_quantity='||quote(old.forward_quantity)||',backward_quantity='||quote(old.backward_quantity)||',tx0_block_index='||quote(old.tx0_block_index)||',tx1_block_index='||quote(old.tx1_block_index)||',block_index='||quote(old.block_index)||',tx0_expiration='||quote(old.tx0_expiration)||',tx1_expiration='||quote(old.tx1_expiration)||',match_expire_index='||quote(old.match_expire_index)||',fee_fraction_int='||quote(old.fee_fraction_int)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX valid_feed_idx ON bet_matches (feed_address, status);

-- Table  bets
DROP TABLE IF EXISTS bets;
CREATE TABLE bets(
                      tx_index INTEGER UNIQUE,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      feed_address TEXT,
                      bet_type INTEGER,
                      deadline INTEGER,
                      wager_quantity INTEGER,
                      wager_remaining INTEGER,
                      counterwager_quantity INTEGER,
                      counterwager_remaining INTEGER,
                      target_value REAL,
                      leverage INTEGER,
                      expiration INTEGER,
                      expire_index INTEGER,
                      fee_fraction_int INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                      PRIMARY KEY (tx_index, tx_hash));
INSERT INTO bets VALUES(13,'7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81',310012,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',0,1388000100,50000000,8500000,25000000,4250000,0.0,15120,10,310022,99999999,'expired');
INSERT INTO bets VALUES(14,'e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42',310013,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',1,1388000100,25000000,4250000,41500000,0,0.0,15120,10,310023,99999999,'filled');
INSERT INTO bets VALUES(15,'3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a',310014,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',0,1388000100,150000000,0,350000000,0,0.0,5040,10,310024,99999999,'filled');
INSERT INTO bets VALUES(16,'a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8',310015,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',1,1388000100,350000000,0,150000000,0,0.0,5040,10,310025,99999999,'filled');
INSERT INTO bets VALUES(17,'194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5',310016,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',2,1388000200,750000000,0,650000000,0,1.0,5040,10,310026,99999999,'filled');
INSERT INTO bets VALUES(18,'72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207',310017,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',3,1388000200,650000000,0,750000000,0,1.0,5040,10,310027,99999999,'filled');
-- Triggers and indices on  bets
CREATE TRIGGER _bets_delete BEFORE DELETE ON bets BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO bets(rowid,tx_index,tx_hash,block_index,source,feed_address,bet_type,deadline,wager_quantity,wager_remaining,counterwager_quantity,counterwager_remaining,target_value,leverage,expiration,expire_index,fee_fraction_int,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.feed_address)||','||quote(old.bet_type)||','||quote(old.deadline)||','||quote(old.wager_quantity)||','||quote(old.wager_remaining)||','||quote(old.counterwager_quantity)||','||quote(old.counterwager_remaining)||','||quote(old.target_value)||','||quote(old.leverage)||','||quote(old.expiration)||','||quote(old.expire_index)||','||quote(old.fee_fraction_int)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _bets_insert AFTER INSERT ON bets BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM bets WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _bets_update AFTER UPDATE ON bets BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE bets SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',feed_address='||quote(old.feed_address)||',bet_type='||quote(old.bet_type)||',deadline='||quote(old.deadline)||',wager_quantity='||quote(old.wager_quantity)||',wager_remaining='||quote(old.wager_remaining)||',counterwager_quantity='||quote(old.counterwager_quantity)||',counterwager_remaining='||quote(old.counterwager_remaining)||',target_value='||quote(old.target_value)||',leverage='||quote(old.leverage)||',expiration='||quote(old.expiration)||',expire_index='||quote(old.expire_index)||',fee_fraction_int='||quote(old.fee_fraction_int)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX feed_valid_bettype_idx ON bets (feed_address, status, bet_type);

-- Table  blocks
DROP TABLE IF EXISTS blocks;
CREATE TABLE blocks(
                      block_index INTEGER UNIQUE,
                      block_hash TEXT UNIQUE,
                      block_time INTEGER,
                      previous_block_hash TEXT UNIQUE,
                      difficulty INTEGER, ledger_hash TEXT, txlist_hash TEXT, messages_hash TEXT,
                      PRIMARY KEY (block_index, block_hash));
INSERT INTO blocks VALUES(309999,'8b3bef249cb3b0fa23a4936c1249b6bd41daeadc848c8d2e409ea1cbc10adfe7',309999000,NULL,NULL,'63f0fef31d02da85fa779e9a0e1b585b1a6a4e59e14564249e288e074e91c223','63f0fef31d02da85fa779e9a0e1b585b1a6a4e59e14564249e288e074e91c223','e0b62f4bd64b1c6dc3f1d82dfe897a83e989b6d7b01fa835f074b5cfe311d8f4');
INSERT INTO blocks VALUES(310000,'505d8d82c4ced7daddef7ed0b05ba12ecc664176887b938ef56c6af276f3b30c',310000000,NULL,NULL,'cf0ea1d313e22ba5f413075b88e07dffc5c00e59f95eeb6d6dec935bd77f5ae4','f06c23e6040a063ed59693baa0d63492dce64e1debc7455b22f5535c9dfbdc67','a2f055f16d61e66beb49eed7edea807f409d9b7a7b5b157ee6d607e6669d7d50');
INSERT INTO blocks VALUES(310001,'3c9f6a9c6cac46a9273bd3db39ad775acd5bc546378ec2fb0587e06e112cc78e',310001000,NULL,NULL,'bdf1308701712d94da26f53fef4c440ea2fb7b0ef7361f424ba9263e747272bd','fac614e6f77f1b954c12523e9d0eeb4252f92f3640f7d067790a510a9e893811','330cbc8becb5f42509b0626017a29deae96fd0051e174eaeb64e95221a26e2d0');
INSERT INTO blocks VALUES(310002,'fbb60f1144e1f7d4dc036a4a158a10ea6dea2ba6283a723342a49b8eb5cc9964',310002000,NULL,NULL,'cf830f949715ebeac09d4441878f60ac04d691c09d6c25c62a0d30fb5886cba9','0c743d61c27efab7c83c1845f6b0446b67c9b59173318709d51363e75e7a0601','e53d80ab9dd913be224902caa951974c26d887ac26210d7765db63ea4ec59da5');
INSERT INTO blocks VALUES(310003,'d50825dcb32bcf6f69994d616eba18de7718d3d859497e80751b2cb67e333e8a',310003000,NULL,NULL,'e881a675a38c4649cd44e6406ddc494996c761671bc349dcdea1de430a84258d','9ae051d14f8d19db67a85c713eefc0a936f1bad818ae1138fcecb91506a46d88','e3906e2d5000b88b8255a9ca58be0fe80e6b93ed034bc2c5295cd9e414404367');
INSERT INTO blocks VALUES(310004,'60cdc0ac0e3121ceaa2c3885f21f5789f49992ffef6e6ff99f7da80e36744615',310004000,NULL,NULL,'13e0c6276f297ff1ca77705f1b18d807ca22f53735fba52f4f5c3766dc4b04e8','a865bc7b6e26b3c3868ae080ab927ce3f2dcdb7d3654ffbcd1b3a8111d0807b1','6742e64136ee2aedcd010a845afdefaf7f75aeddd2acb7d0cd7db6ef1ee3b7ae');
INSERT INTO blocks VALUES(310005,'8005c2926b7ecc50376642bc661a49108b6dc62636463a5c492b123e2184cd9a',310005000,NULL,NULL,'765896f532b411af9f889687a750d44414296c20002f3e2abed9551a6822937d','59095fce5f573c2ff1b5eda5cd75c36227b0f9782601e7538215fea5317c505b','d8907c738e3642e41abd416de9527265807ba24e05ec15a839522509be340e7b');
INSERT INTO blocks VALUES(310006,'bdad69d1669eace68b9f246de113161099d4f83322e2acf402c42defef3af2bb',310006000,NULL,NULL,'853e3a8d39c4e8bdb36a0ec01a8d20f12335fcc00a00ac271e9d83be471d394f','0e5bef0b94b379484e3a9ab8760bc92545571f77dc01ba9be2d6b2791eb5614a','51443ff382ce5f136b49a4ad4a6adc01e8e1d14fe005a421d4989ca297043e3c');
INSERT INTO blocks VALUES(310007,'10a642b96d60091d08234d17dfdecf3025eca41e4fc8e3bbe71a91c5a457cb4b',310007000,NULL,NULL,'f2b2d250a94afa158f9ed84434c3ac7a0bfc97b4387e5e3c099afc95b8a6ad9c','5e2484ed363abe9fcf41cacb16d232aaf1eab00be637b8214d8346beeab3c8d1','d93e97880eee09f4924c6aa60d90c521e6a0c61686b4619e71a9da3b2ad4f36b');
INSERT INTO blocks VALUES(310008,'47d0e3acbdc6916aeae95e987f9cfa16209b3df1e67bb38143b3422b32322c33',310008000,NULL,NULL,'8c44f15f5606b6fe984a9fa7df8d7d5381fe87a6c8b634469804328885668569','e375890958eba15170caab7a1462b29e2ff138b6bc6b86d0cf2f1b9553fce75d','1706cb7895bb6e6d46e6504b5842204258800b196ef212ea054844c1061b71fd');
INSERT INTO blocks VALUES(310009,'4d474992b141620bf3753863db7ee5e8af26cadfbba27725911f44fa657bc1c0',310009000,NULL,NULL,'ba378e9192f290d3f9d3dd1e46aeef3a185bd5aff1be809c8974fca8dc142987','440fcee000e6c76b81a834f90cf932c4de93e022adbf239a68320e63bbfd555f','ee71be42c4de040d01fb6c6b66396ae25dce573a871277079f111546e62577c4');
INSERT INTO blocks VALUES(310010,'a58162dff81a32e6a29b075be759dbb9fa9b8b65303e69c78fb4d7b0acc37042',310010000,NULL,NULL,'64f78f9eedce2931aedfe413b4f4bdeb728752e1c897e0bd44c7db665976a723','f42a5ace9900e8bd875e2dcd316b32472cef339c1144c2e2f57463d3d2032cf6','2a863dec52ec7579b7c1c14e385c74392d412ac98cf100ba954cd4e39e137868');
INSERT INTO blocks VALUES(310011,'8042cc2ef293fd73d050f283fbd075c79dd4c49fdcca054dc0714fc3a50dc1bb',310011000,NULL,NULL,'671a1b4e1edd1f96dcfcc96d521fb2125ae5b9d2d01a76fc66686b7ed20c5662','dd8467d171f53cdc75d4e1f7e868a35dc8bf86dea65ffa30926a6c08d0ad9482','50971904f0e4306f56cf5b011eb395ab72e9fa46435ed967079b13b046bf83b5');
INSERT INTO blocks VALUES(310012,'cdba329019d93a67b31b79d05f76ce1b7791d430ea0d6c1c2168fe78d2f67677',310012000,NULL,NULL,'1f5b502c341699b5a59b87566c0fc02b7db5c657919f014e41a00303aa53efc8','ae91db261f623fa872686b899dde2f143a760188b30eda53d75d845d6f2ac512','e79f5c8c52c650896ca2518d8cf26e1e112c005cdda65148eb4138cb5430b24d');
INSERT INTO blocks VALUES(310013,'0425e5e832e4286757dc0228cd505b8d572081007218abd3a0983a3bcd502a61',310013000,NULL,NULL,'cd0cfff6de5dd4381301929c740015d5910339ba915a83eb4229ecb91ae84c17','d5ed3b70e31d2fe5d430bd85164c24f968d0eec4ef4ec4fe25bed76bfa24086e','dbdb6324efb5f048cce3fb799e4f033d1ac4238059c7c9c4fd75c5cc230dbaa4');
INSERT INTO blocks VALUES(310014,'85b28d413ebda2968ed82ae53643677338650151b997ed1e4656158005b9f65f',310014000,NULL,NULL,'5012d84065c7a39b5563f4fadeaf30670b47df3856f43d40fda74de663753e4e','6ef29857ba4ab9ef8ba1e2f366c4832d0c61925c5fec136b99c8422816e619de','d69a5f0f25e478cca6d1c2dc6741806d92b069908f9ae136fcadfb63e38ea50f');
INSERT INTO blocks VALUES(310015,'4cf77d688f18f0c68c077db882f62e49f31859dfa6144372457cd73b29223922',310015000,NULL,NULL,'0356494d376b2b65b9f4b066b9d2baf2ae90d82369b87914bb58a67927ced5af','27961c02dffd90c98f8f8d6e4ec8e0f93f3bc0790e3c52b06645b6304e0ce19f','9692ac80a135c454c10aa820b4073a6c4de6f487cd40b2800040a032295f26a4');
INSERT INTO blocks VALUES(310016,'99dc7d2627efb4e5e618a53b9898b4ca39c70e98fe9bf39f68a6c980f5b64ef9',310016000,NULL,NULL,'c90ff439bd04970ed9e6e25cbfce32160450925a37ba3360f40df8854529b52d','ced209dcc88e9595dc986de392d621fc24fc7cd01fdd8305ee1ddc07beca0c45','8ee2d2e66553b16d47c8dce6c9f15cfcb8c1a4fc026144f12bca8c78c1372e5b');
INSERT INTO blocks VALUES(310017,'8a4fedfbf734b91a5c5761a7bcb3908ea57169777a7018148c51ff611970e4a3',310017000,NULL,NULL,'19cf18f708dab6a983a2642802deb38d25b6fc205ea663059a0569fa38bdaf8d','d44c7d2bc4599cda71ddbf4b40cd46e8bbd8bfced9526b7580d0f9d5c5235812','f574f593343287fc5261adae940571292a8ded1426d15d40fd509932fbf6c437');
INSERT INTO blocks VALUES(310018,'35c06f9e3de39e4e56ceb1d1a22008f52361c50dd0d251c0acbe2e3c2dba8ed3',310018000,NULL,NULL,'d9ac565fbe7bf18c1d899dab8e0c98e070880e36fa51710382017d46ddf837cf','3704b37f23d272e5b7550c999cdb981e6874a4c40764bfd6e38e38b79743603f','0cc3d551e30bb0d03df456a60ba96e93987fc0af3684fe365d220c5bde6ef27e');
INSERT INTO blocks VALUES(310019,'114affa0c4f34b1ebf8e2778c9477641f60b5b9e8a69052158041d4c41893294',310019000,NULL,NULL,'b66661deef419a50557d171cc1bcae04f5bc260ed1f5ff56cf08ef39158617a1','515fead3a4dfdb2ea3459b50fba7408742b8c0b97330afcceb0b59e96a755b64','b0d8cdb116d24de70235b5a72710d0be64b762c65005b3bc0238f16d56f9f40e');
INSERT INTO blocks VALUES(310020,'d93c79920e4a42164af74ecb5c6b903ff6055cdc007376c74dfa692c8d85ebc9',310020000,NULL,NULL,'57a6c53e41338011cb06cd60118961dcec0e800f62a2c4b1e9381c666319680f','35136b2d8a9e59de8206253a981995af4a9d6d1b8fa75fd314f63dff4bba355b','ebb275ebf3aab76a9fa726b050fe423bb79bde2a03d0a707a917181395b0268c');
INSERT INTO blocks VALUES(310021,'7c2460bb32c5749c856486393239bf7a0ac789587ac71f32e7237910da8097f2',310021000,NULL,NULL,'66c16af10125f298796da828f1a6c2b43123cda38e3dfc57ccc25b00f3da17f8','e314ee76e77ab0ebe5384e7f9ab466e9f0608a7adb42d6a41c18f7aea94967b6','1bf94022e1b8516a05ea21daf1fa93d73c18bea686cee74b8d5ef9e5a7056ad0');
INSERT INTO blocks VALUES(310022,'44435f9a99a0aa12a9bfabdc4cb8119f6ea6a6e1350d2d65445fb66a456db5fc',310022000,NULL,NULL,'43b6213cad601a389aed2a4e912be118dfab6cca5358d86bac03f4bee6765493','1fec6d17ee40de5cb95c17d8b97a6a16ad6d57e541acb4106f4e09b8ba7b5970','a25824c407ae057694dc0504bf466fc495c5aa0207f34055dbc742ecb3ec73eb');
INSERT INTO blocks VALUES(310023,'d8cf5bec1bbcab8ca4f495352afde3b6572b7e1d61b3976872ebb8e9d30ccb08',310023000,NULL,NULL,'8a9758963891bbfbdcb6515d8d3e49c941fedba7de82038776e9f8ed65e803c1','b48784020587abce39f27a48b263afc4da76f8841458fdf7672ce8461eeff673','33b2aff548ce61d562478e810fa6896af86b031753029baf67903f8a7d726a5f');
INSERT INTO blocks VALUES(310024,'b03042b4e18a222b4c8d1e9e1970d93e6e2a2d41686d227ff8ecf0a839223dc5',310024000,NULL,NULL,'cb034ab4a3e252fdfe9973a672e208295741a52634c9332b1501d612e0012e19','edce98e12617b23ec67c43b73875d2c2b138516eb76e688fd9dabde95b329cf6','049325864913286813537fbda7f2a3b4670fc37e4b1390cc15675e8573756de8');
INSERT INTO blocks VALUES(310025,'a872e560766832cc3b4f7f222228cb6db882ce3c54f6459f62c71d5cd6e90666',310025000,NULL,NULL,'5addc8253469d5c729cdffc1c637b75d9e8886a633d4406dedf2b1c16ba5b92a','d2a0421a1cd5416492439cb0b80788e2f89974e36ec6372ae70277d08a7eb3a5','117957961777d3b755deb3f03baa44ef270407401f73d1c76ed3ffe48fbd1871');
INSERT INTO blocks VALUES(310026,'6c96350f6f2f05810f19a689de235eff975338587194a36a70dfd0fcd490941a',310026000,NULL,NULL,'8620bd0283c320330631185d1b2351718f174732bd099324a0880719cdfc18c7','2860ba6ea669859b0434f637d2751af496490f53d2b53fd2e45d368080a2ee98','07d8419569c9c32029cf3cf3b006efbf88cc8665c3d4f350b1750415f8e1e09f');
INSERT INTO blocks VALUES(310027,'d7acfac66df393c4482a14c189742c0571b89442eb7f817b34415a560445699e',310027000,NULL,NULL,'96960e09478184f4f0ad38d1fc03f0c0240e58715a0a29745a6dc58c40003249','0ec6d9e5c042ae5aa9ed4d8c228b85214aa43dbfe721b8c87210649cf44e0f88','907a56a92ca1116a5a33d4a461893f616f559b334f0d01db07c0d15f6d7518b1');
INSERT INTO blocks VALUES(310028,'02409fcf8fa06dafcb7f11e38593181d9c42cc9d5e2ddc304d098f990bd9530b',310028000,NULL,NULL,'2f556d2528abe1c4e9d31f6ed70d400d94633d4dfb54c9a4f250e1b054f9a384','bca48559d5a1dd70e33f9bb9946c52aeedd1da1fe543bf7ba0a4385939723788','697a1856f62334494175e061feaebe2ed67c0c9659f90b69261d51cea7346592');
INSERT INTO blocks VALUES(310029,'3c739fa8b40c118d5547ea356ee8d10ee2898871907643ec02e5db9d00f03cc6',310029000,NULL,NULL,'be195b1f7b7b55dcefb83907d954736d4bf059a9e32055131efd16602d7761d6','002c8d49738eed574741be3d5b1a31789914b071e3ef0aa223f989dbab465613','008ab5636052120f5db4da0872e1558776e0ea4235658442446c1007f9810c64');
INSERT INTO blocks VALUES(310030,'d5071cddedf89765ee0fd58f209c1c7d669ba8ea66200a57587da8b189b9e4f5',310030000,NULL,NULL,'d3a25656dbb63eecf1c89820581fcab193d750f3a09ca8ab34a5008c8d89051d','fa3875ebb006b28e41f70dfd6816af027d89d05c56a07fe65304d7fc7843585e','6f03ce85d73f0b5bfb54534fd2594aa0790e4013e69ba58a611ba031478369ff');
INSERT INTO blocks VALUES(310031,'0b02b10f41380fff27c543ea8891ecb845bf7a003ac5c87e15932aff3bfcf689',310031000,NULL,NULL,'0edb535f8c6a40062a86e4ea327cf7fb70310b6d55a6654d5a23e54498aa3159','8ab8856ad0953199b426602812448f66c507ad41a3682200c0f8847c2d72cedb','6b40b997d716c01658093e04212704e7ffa34beb89603d823073e46bc325a6ca');
INSERT INTO blocks VALUES(310032,'66346be81e6ba04544f2ae643b76c2b7b1383f038fc2636e02e49dc7ec144074',310032000,NULL,NULL,'a9208a1b7f782852d652e5089c6485744031176b4d285ea985bbc1df0ccf49c0','30580abde3fbd33149d0cb94bec3b29173092fae3c592e6d119ef3549d6dc1f9','1ae82ab402adc89a892521c915a55ca28e3319b7544e00fbfac8aab15821139f');
INSERT INTO blocks VALUES(310033,'999c65df9661f73e8c01f1da1afda09ac16788b72834f0ff5ea3d1464afb4707',310033000,NULL,NULL,'c8a973eb6bdd28dcab4f1b2a5e29e104944745e57a54e6d87b370aafb2e589f6','9cc3207a0588975c2504c90385962f09918ea096d0a84889b09dbb35453805c3','89f2c768339e922faaa061b82a95b2f53c77a3f282d7d999b6475efadb2dc6b8');
INSERT INTO blocks VALUES(310034,'f552edd2e0a648230f3668e72ddf0ddfb1e8ac0f4c190f91b89c1a8c2e357208',310034000,NULL,NULL,'0d7b5809b7a5aa5ff854cfe141490a78c9b33e16f8102a8e804dbf0a0a8c0842','57fca9b1f25e262957b38cf679f137dc8ba8e7219c67a2fe85a02136972ee682','7f57ebc3b07f7bb7dbb73e2a5553b3cc97bc7144b29007dd8e0bc87b8ed19024');
INSERT INTO blocks VALUES(310035,'a13cbb016f3044207a46967a4ba1c87dab411f78c55c1179f2336653c2726ae2',310035000,NULL,NULL,'6b4c99289086445a7bf575110172a661c1cd37c418b70afd8ef3be0982041f5e','89f634f238edeac3ca3222d48d60125725d121e980ffbc7d8c64913f1abef704','39216607be1b12d271a3e8ac1d1fecf98ef1421646f16c6510198da8802a5553');
INSERT INTO blocks VALUES(310036,'158648a98f1e1bd1875584ce8449eb15a4e91a99a923bbb24c4210135cef0c76',310036000,NULL,NULL,'f20b81389b2f4c9c9be4442b3c68f87da881406f1490637c7d93d63539155a7e','68887900af514d9af1fcd7ddf255b2b5bfeb199d34b9cff66125baebc125ecdc','0c25c6f90d70bb3ee04f8d259031dcbd88495863fcdd66188706e2aa4ba6e621');
INSERT INTO blocks VALUES(310037,'563acfd6d991ce256d5655de2e9429975c8dceeb221e76d5ec6e9e24a2c27c07',310037000,NULL,NULL,'52d554e6b53b853066a3a8f931fc37779f3596c4388e277a9f66a95e001a09eb','e445d02286f02f36ef8db98c3026b66dd31ab163c707a27ec11c28b4c1717c6a','c7903b100fa309cc8fb0f50321ff516d52c92eb9b797d70bc6e3ddf92817c212');
INSERT INTO blocks VALUES(310038,'b44b4cad12431c32df27940e18d51f63897c7472b70950d18454edfd640490b2',310038000,NULL,NULL,'08a949af614ff73a79313a5a949908b368efe1f8c131eeeb51ed610baf65ac46','f9d36e63d52df67bf676adaf8c2bb33c1933146f73508fb7d5e2e7dda5f75ca8','f3329328648688b958dc11586ab862bd81ed9d143c4aef60a5a9d800abe7856b');
INSERT INTO blocks VALUES(310039,'5fa1ae9c5e8a599247458987b006ad3a57f686df1f7cc240bf119e911b56c347',310039000,NULL,NULL,'7ff8b2408ee1124a5ee573d31023660aabcdb21599bdcfb4a3bc1895d7910094','959a04a0af3ce357579b66242730c55b4fd9b8d8e9ff15c7dc9598637778af4a','d9405829e8b2067e5b698d644a72035c0ebea42e2321887398c0d98b5d0e2d63');
INSERT INTO blocks VALUES(310040,'7200ded406675453eadddfbb2d14c2a4526c7dc2b5de14bd48b29243df5e1aa3',310040000,NULL,NULL,'c687e753c01711e94cfcad1f16d2976a12ef5d6c3731c64db26f969c988fe7c3','b769b7fc526ae8b8e8e3ae86d31422677f99239ca7cc6b70527698bc1fb237ea','5c5a0391f2a4f2af136feb85d67cab704a4ddac93690efb607d6cb1181c4472e');
INSERT INTO blocks VALUES(310041,'5db592ff9ba5fac1e030cf22d6c13b70d330ba397f415340086ee7357143b359',310041000,NULL,NULL,'66f493ec8b5cf8140d1f627f008c50624d3069f56828df90286b53a2d6cbf47e','47c5243a61cf785566b8f5d5a66b224920c852823f257a63b901077f9d51546b','746aac3a1310a8f0a83d3e3e87bf3100acb10fffe2ce5c3cb83971c0f2fc26a4');
INSERT INTO blocks VALUES(310042,'826fd4701ef2824e9559b069517cd3cb990aff6a4690830f78fc845ab77fa3e4',310042000,NULL,NULL,'33acd319bde452aa81b589435a31ee3add742870a928ef2c15a7a447b4b4e0fa','9da12518d3995d6492660ba7e002e9aab174fb55337be74024b6c6da1c387e53','20aa48aa60af798ea290e7b1206e00ffae47d04d367183812ccbf68552b6085f');
INSERT INTO blocks VALUES(310043,'2254a12ada208f1dd57bc17547ecaf3c44720323c47bc7d4b1262477cb7f3c51',310043000,NULL,NULL,'83997825aa2597adb0292e265f01e937f621cc75d8cc18e23a4bd0c1fb0920c7','b84f1b4532ed38bcb6597512e9cf7420b9ce91fa403a152f9ff2405dad704602','10fdb39cc8cdad9c8cae11f585648d245673e4d3cac14972b75c242aa3ef7a40');
INSERT INTO blocks VALUES(310044,'3346d24118d8af0b3c6bcc42f8b85792e7a2e7036ebf6e4c25f4f6723c78e46b',310044000,NULL,NULL,'9890bca86442f329b2abf1b3bbf4d94e8ab54d10dfa7823a53f02fcfef030d88','19325d90d9e72412d7ad7f42b0b423d3bc6d6c4f0503670f90707c652c731c60','d3f582056a63cb76bd83a2876a4457e894dcdc7ad5678f14822f3a17c1d0bd9b');
INSERT INTO blocks VALUES(310045,'7bba0ab243839e91ad1a45a762bf074011f8a9883074d68203c6d1b46fffde98',310045000,NULL,NULL,'a909f658a8f405ef1f5cd8bbab03cbd865235544ae1c2f4dc20e2a4393181efc','c43d2952286f9137127897b3f2712292ccc07a990e69675bef88f1dcfc709488','a066272c3d565ef73fdf022b2d820b798a38225afb79b7744ad8337f2f656b92');
INSERT INTO blocks VALUES(310046,'47db6788c38f2d6d712764979e41346b55e78cbb4969e0ef5c4336faf18993a6',310046000,NULL,NULL,'713d2ccc66a1aa7797ea9b6af18b04245478c7582a8aee76cf2c7f3f3060df3a','6abdc9d57e166f48e040fbea040b0456a0a04f4dc45d26387161f45c42a233a3','f1483307ef8575900b9b4aa3bb028ddf40282e49fe6db439fe0a0bf6dfbfe81f');
INSERT INTO blocks VALUES(310047,'a9ccabcc2a098a7d25e4ab8bda7c4e66807eefa42e29890dcd88149a10de7075',310047000,NULL,NULL,'534500ae61a04841771193d57384d27b54fa2bb92c0698beaa46509b3d39eb1c','ddac28fdaaddcdbed1732408c8743caa61ba494f1576279305b1f2d77c713d32','b488fcf6ccc56394cb31f6897f80f0f76a169f767169b1278fe1e4b259b70592');
INSERT INTO blocks VALUES(310048,'610bf3935a85b05a98556c55493c6de45bed4d7b3b6c8553a984718765796309',310048000,NULL,NULL,'48c8e5d9ab1887f092731ba2881a330d22d4f03f601dccc096fa5147042a3d55','1eb5596099cdca933fc24f128448f27e2add69cbfc44a493d4cd3c34513fc15d','cafcda6b9083cdb095e251b16994c52b9da0521ba7ce9907dea2aef9df285773');
INSERT INTO blocks VALUES(310049,'4ad2761923ad49ad2b283b640f1832522a2a5d6964486b21591b71df6b33be3c',310049000,NULL,NULL,'6c5ec3d2b7d8a724175559db977cb9ab78eecd39b9239688b30d6d3350cb01fe','b99d288457a5f2e5d53cc4da883069f7e7241d57b574ec0ce57076310646d2a6','4dc4e5fb12824bb963dfba4bfe971d99adedfdc1a122bc27902ad9ddf3bd20cf');
INSERT INTO blocks VALUES(310050,'8cfeb60a14a4cec6e9be13d699694d49007d82a31065a17890383e262071e348',310050000,NULL,NULL,'817dc86594b3820de76f1d2bc2400d702475d558d6ee5bef4313fc154bbdaca2','4b2fab5ace6ea870c92fde81ef9a758774667f943f8d62ccf759a5d0aaa84d7c','a0093845bbe5062b97156d8d6305936eac18962d855817960e9d35dad194ad12');
INSERT INTO blocks VALUES(310051,'b53c90385dd808306601350920c6af4beb717518493fd23b5c730eea078f33e6',310051000,NULL,NULL,'00916e6bac2f648f953c8d6dff21438a6ec53ad198b33f90667e8d4564e00e78','170c1739039de8a10e7ba4bbdf0cf84a6907080c5bbacbb9b147557a20cb9393','d943a674b814b45fc88693a6e78a61c61c837a9c2c78a2889d23dc490b4eaa98');
INSERT INTO blocks VALUES(310052,'0acdacf4e4b6fca756479cb055191b367b1fa433aa558956f5f08fa5b7b394e2',310052000,NULL,NULL,'959df962b9bc7ef215f1530b886613404adaf81552d6eeb4b1401ea265ad5f4f','a9762d8182d9a3fe62c758aa4f9728ed47ba929e9e3dca0b59bb31055884ed9c','6f27ad80347b0f457119208c1b0e783c80ecc8ec01af100fa077fa8fa5cf3522');
INSERT INTO blocks VALUES(310053,'68348f01b6dc49b2cb30fe92ac43e527aa90d859093d3bf7cd695c64d2ef744f',310053000,NULL,NULL,'d76b639ebddd434e5269de084de0b502e7f0eaff71b4e99de2d4ebdd1fc61380','9f0351be178b51d17618ddb6b8c320a6bb594355bc6dc43f9ac8e21c11937e83','8fde135c33d29c3958ded92a539b6174422dfaffe5b90dd40cccb54792f05f29');
INSERT INTO blocks VALUES(310054,'a8b5f253df293037e49b998675620d5477445c51d5ec66596e023282bb9cd305',310054000,NULL,NULL,'525e8cabfc993080d128faf38a5e5c9e9afa61423a5f20a90d68cdcacc96b59b','80ac745a315b4ff88be697054813e4fd1c5a43ce7b5dc099558fd89be277bcb6','f1d092397e0107215b3de8349d1333a6c8e1e91c3c943234d01017500c23667c');
INSERT INTO blocks VALUES(310055,'4b069152e2dc82e96ed8a3c3547c162e8c3aceeb2a4ac07972f8321a535b9356',310055000,NULL,NULL,'155ffdc74a2077a3da7d5c068833468c7d0758dfb525a799f910cdb1543beadb','099c33278886ec7fc298e41d8d61f74f85e74b45fda5343ba4781c72439e3a84','80f3ed9320a4d25ff05857a2afc94b405491751ada74e5b2dc91ff9333203240');
INSERT INTO blocks VALUES(310056,'7603eaed418971b745256742f9d2ba70b2c2b2f69f61de6cc70e61ce0336f9d3',310056000,NULL,NULL,'4f6fe786e34af90927bcd888b4b2a8fc69d3ccdfe4c4bb37edb2007901ce234a','4a3d978e18747b977129b888e25f626adfa6d2e4334f48d59f02e5eda1ae26a4','f9da6b3c03e8b2705a62fb7bdc790967ae556d5afa58cae9310c070d924a4a6c');
INSERT INTO blocks VALUES(310057,'4a5fdc84f2d66ecb6ee3e3646aad20751ce8694e64e348d3c8aab09d33a3e411',310057000,NULL,NULL,'30978d87fd8e32d9d27c92a0d4ca19d179b515ed95410fa96bf496b4cd8aa5e2','c2dfa054168ab204a330d93bdba9f4c1fc04a4e36432981db45236a45298974b','39d03948fd6cb121faf792608129756de76eee0590130d8f4cd48bb31f7f679e');
INSERT INTO blocks VALUES(310058,'a6eef3089896f0cae0bfe9423392e45c48f4efe4310b14d8cfbdb1fea613635f',310058000,NULL,NULL,'a0760bc5d2f04b381cc46aca84aa3788e8e3fbc833379a26ae812807d3a04fc5','893cba6df41efef6360af9a31bb9fa166af8bfd1310c3cdd703cf5574ad27fc4','c225659a81b24b4d00c9763ab28c401c39f08f995e659c29e7c8defbdb18629f');
INSERT INTO blocks VALUES(310059,'ab505de874c43f97c90be1c26a769e6c5cb140405c993b4a6cc7afc795f156a9',310059000,NULL,NULL,'26dcef9e54b1a34b6024f8402ddebb6e9449cd90c270e3db75354a001484b1a1','e798643cd05b4fbaa6153013df5b82cbb9ccd6167774c4a344283dfe213b9495','923e0a9e11efc8610bf08536f099dd85a36ba0b85c8e74b74a008ceb65191688');
INSERT INTO blocks VALUES(310060,'974ad5fbef621e0a38eab811608dc9afaf10c8ecc85fed913075ba1a145e889b',310060000,NULL,NULL,'810ebcdb63a08af5a26d1fd4e7a3604afd03bd06ff620d6a86c665e1c81116d2','e27f5a7dde568506521e1a83818bc9c96fd925132f9cc34d229de5b4905add3e','08e915ccc772d1b6be61dbbe6d87c3694423f0b215488052adddcdb068eafdd7');
INSERT INTO blocks VALUES(310061,'35d267d21ad386e7b7632292af1c422b0310dde7ca49a82f9577525a29c138cf',310061000,NULL,NULL,'1edfc24d186c7e7267b11c03b0a29e57926e9ab25f668231a18a499cbd08c702','f944746dfce89ceba62233ae4865a99294e75902502ba0c3efbccb73ba8b4220','989861d8a822935474e88b4f92a6b6a3261c39f6f2dab145116d3af7eaa5f3a1');
INSERT INTO blocks VALUES(310062,'b31a0054145319ef9de8c1cb19df5bcf4dc8a1ece20053aa494e5d3a00a2852f',310062000,NULL,NULL,'b0de9503f019c9548a97bd198e6b1b58b57d6a7c231ace2d72adb0421b29e9b7','e56ba63440c19612cc2590a0e432f0a7a52f582b928c225f44ebc02457e0c44d','f09933c51c436eaa4c5c9d9b7ed5404b5141281332e54ae2890eb987983ce79b');
INSERT INTO blocks VALUES(310063,'0cbcbcd5b7f2dc288e3a34eab3d4212463a5a56e886804fb4f9f1cf929eadebe',310063000,NULL,NULL,'62e41caff168eb4b15eb67ab2130510ba3f17ac186f8516cf5b5c6f168988345','5b7cd269a8f33da494f8d14d87a9e5133503940366154f41b4c3faa43c577f53','a8ef027cb3312e7d7ff9ababc2de51d854fc63d650f7945047039c1234223f1b');
INSERT INTO blocks VALUES(310064,'e2db8065a195e85cde9ddb868a17d39893a60fb2b1255aa5f0c88729de7cbf30',310064000,NULL,NULL,'a444b1535d27bb2917478019c4c59abf9474e87128f9ec1e44c20eea1f014f3c','09de3355483f56d8115d88e00ed42980217850d2fed3ebf3a5533e07aaf18908','f6148691ae6634c35cc644102f4d5445b8cadef7b5dc402eda794300b45cedaf');
INSERT INTO blocks VALUES(310065,'8a7bc7a77c831ac4fd11b8a9d22d1b6a0661b07cef05c2e600c7fb683b861d2a',310065000,NULL,NULL,'0ad978671f587f99e5e1c1b6f68ac3d18bb03a3bd7ea9afb63590bcef25160c8','651e32ce99255bc371cc317c1d074cef39305cd5bf532a6c312227fc661054a3','74a53eada7d20c8a0b02932c5ed8fdeb7d37acd777a23c1ab6fb8f80e73b183a');
INSERT INTO blocks VALUES(310066,'b6959be51eb084747d301f7ccaf9e75f2292c9404633b1532e3692659939430d',310066000,NULL,NULL,'a6bb36829770b24fa0b960b85566a0138360a60b52cec62d94d7df8cb0b8f8b4','55529acd430a07f4ec7922ccbb468554ef635abf469a9f6d632798c2458ad352','7f5421346eccd6cd51637aea4576982d78b7f090c35e9f3218a574877d3d093e');
INSERT INTO blocks VALUES(310067,'8b08eae98d7193c9c01863fac6effb9162bda010daeacf9e0347112f233b8577',310067000,NULL,NULL,'9b8ceda9b170429d8b9ed517f0db95487b3058397e20d7e786577c8e46b389b8','cc86dc3ad2812c772445c6ab4f68af5ac2e99113d2e8d3db73dc1c7198f79d92','8540f55de23337415e2c126f2ed64e3faae33b753c711df60638bd334f9c6f2e');
INSERT INTO blocks VALUES(310068,'9280e7297ef6313341bc81787a36acfc9af58f83a415afff5e3154f126cf52b5',310068000,NULL,NULL,'cee2e41baf86f1af24d555e9ab4a0c023b5f1ab2b054707d4434b4f60d31862a','a5594f5cde5e8bc6108a589a0e4c000dc76e978db1b0acfebbe067c0cbb298e5','fe8127bfab0d841af1946a539812d4a66dcd3991668207220bb1693749d40a3e');
INSERT INTO blocks VALUES(310069,'486351f0655bf594ffaab1980cff17353b640b63e9c27239109addece189a6f7',310069000,NULL,NULL,'cbfd7ff728f05ba3f1db5972f1449618a79d3fd0d76bf7fe990aed2eb2316a38','7d6e4b5fac905776aab66415905216d0c4c85e06816a088a04edd7f59d424634','15af8bf5492941e2b04762059c21b09ac4a4abd6556520fbc8b9ada15b796550');
INSERT INTO blocks VALUES(310070,'8739e99f4dee8bebf1332f37f49a125348b40b93b74fe35579dd52bfba4fa7e5',310070000,NULL,NULL,'9af85cd995c83b5a5f0cac66351cabdf9dc9faecfee080638fc76019663faaa6','98149b152feeda43fb2180cd85b6c42a8d4ca20bebebed2ab064dcdba2bb1ee3','0c88fa7466fe350024278414e97c79f19a8f1de2e85afa7d5bba38463bfc9279');
INSERT INTO blocks VALUES(310071,'7a099aa1bba0ead577f1e44f35263a1f115ed6a868c98d4dd71609072ae7f80b',310071000,NULL,NULL,'a3c547e84db6b29630b87fa566e37796e0632ba616dd6d521d558632c3b55370','a6ebf8e56dfce11b4c3568feb978f113023cbda767d6670a6a11df00d4252ad7','3faf9703a4dbb0c0b1a480edf1ece6262518ccc660c764109183641e51d91566');
INSERT INTO blocks VALUES(310072,'7b17ecedc07552551b8129e068ae67cb176ca766ea3f6df74b597a94e3a7fc8a',310072000,NULL,NULL,'a0170d8a72a0f8642c0863899bf034e754596e3fd8ddffefa91e7e9a7addf944','a7359f29b8b137963dc8d5faef3405e5a8b0f7fa298b0a1df4183b7c8e438190','39d9b04498f9ff90fea3d8bcf8452d7c3e618c3997eb7b2d55159590080d914f');
INSERT INTO blocks VALUES(310073,'ee0fe3cc9b3a48a2746b6090b63b442b97ea6055d48edcf4b2288396764c6943',310073000,NULL,NULL,'e0179a21342fcf35fa169567f1ef35bd6b0b1b048a98e90c049fdf3ee58e9da4','a105966804b89cf1bf4d212b0e2b42068b5f756306d0484ac8702879b2db2446','222be649143e7bedf8e87c29dc0c802d9334edc9cc8ee4b7ac1d03de8fd23f7f');
INSERT INTO blocks VALUES(310074,'ceab38dfde01f711a187601731ad575d67cfe0b7dbc61dcd4f15baaef72089fb',310074000,NULL,NULL,'8855ace296b0b078d90aa24fcd30ca9f9cccf9d3961f3dba4985a3ff187a02ac','86c702b795ba2d6825c88fece424fb3bf809c30f1af345d811b8aa5a90112a3e','b5d571cb81587e6d64696042e99b12078c50ce676dde176cd99121329738a97c');
INSERT INTO blocks VALUES(310075,'ef547198c6e36d829f117cfd7077ccde45158e3c545152225fa24dba7a26847b',310075000,NULL,NULL,'bde3a6c6cc31b96d58f466d3ce0361cc6366c8c239778f21b696d4063cf6d89e','e82d777661dee32f49c10e2f19e8d61567cd7ec505354f4a8e52fa3fae34d721','e4222f1beda0bf84b46712c2df6f31ae52bd4fccc8c735dc97a2a5964b395c97');
INSERT INTO blocks VALUES(310076,'3b0499c2e8e8f0252c7288d4ecf66efc426ca37aad3524424d14c8bc6f8b0d92',310076000,NULL,NULL,'f562851b32a7005ee02b9e2491c0195dddce451e8fecb428209d087e69345303','08e091bbe5a76261e52373c7e314ed86e4c38aed457ecb3861b1d33b909b1df7','d95423841460896954150b35c869a89e76b6f8692678c6ef08eae12dab003d83');
INSERT INTO blocks VALUES(310077,'d2adeefa9024ab3ff2822bc36acf19b6c647cea118cf15b86c6bc00c3322e7dd',310077000,NULL,NULL,'996cda7b65e623747deef936d61491cedd0159f44faa1e3536de1b6d6c474097','e3924bbd16c6cc429d71018f96b294e0906e4c917ddeb5c2fb951700075477eb','2b3d9900a64643d51192596e47876788b23cdde7227eede8ec18ac31a09eee33');
INSERT INTO blocks VALUES(310078,'f6c17115ef0efe489c562bcda4615892b4d4b39db0c9791fe193d4922bd82cd6',310078000,NULL,NULL,'c8286f73cc3a070f4251b7c59bb485e611437a1916fd39ffac831dc78df54ecd','210076137d8912a48d1783ff6de2ba3c8fbc83b7af76b4e5ad798c5044df25de','41b3d170c54cb493d91dc25ff00bf7e9ba1778c9278e7d73b8c3722fc38170f1');
INSERT INTO blocks VALUES(310079,'f2fbd2074d804e631db44cb0fb2e1db3fdc367e439c21ffc40d73104c4d7069c',310079000,NULL,NULL,'ef9dab42700918027fac849f2088d2248a6291dc7bc24be583b556f37739631b','f9a1afdb1aa6020af679509cc233aefb9f074b9a77383d32bec3b848afc2ea31','d11536f1abbd3c05370d3234089bc93564bfe3644216e90d2fa67f52376a78c9');
INSERT INTO blocks VALUES(310080,'42943b914d9c367000a78b78a544cc4b84b1df838aadde33fe730964a89a3a6c',310080000,NULL,NULL,'c6bbc52f1e8f907b2d66378f4352f41ae3d354985aaab5f16d737d75a7e6b1d8','c40665482bfa2a8c2c2785499e779fcddfa0694bbc65ebf8f076219a377201f6','449892e94c4a8cf4868b56f5e2fde50a31e063e3c7e4f404b68b075a419b8b31');
INSERT INTO blocks VALUES(310081,'6554f9d307976249e7b7e260e08046b3b55d318f8b6af627fed5be3063f123c4',310081000,NULL,NULL,'66f7b7ff8f0217ed62938a5931d4a6a232546e5d58e09dfd3ba5a792c35fa560','5173550ba3fb451e3ac206f9f4a16f77abc40bc0634a9c5426445c913abb4a50','b8e5e5e620ec9feb36703b9dba884c9cbf79f6a0e0ffff0d079f586060da2e3a');
INSERT INTO blocks VALUES(310082,'4f1ef91b1dcd575f8ac2e66a67715500cbca154bd6f3b8148bb7015a6aa6c644',310082000,NULL,NULL,'2b26c6d901ca9790987331432372046d9620d10ea163f4824208d6b23e8e7a35','96d3149f331029f0a861133326fcb21affea1310f7e03811ad522f19c3f2013c','e2335700e3d3a8760f76383b4b1a1450f5db43470988409177db85518de902b1');
INSERT INTO blocks VALUES(310083,'9b1f6fd6ff9b0dc4e37603cfb0625f49067c775b99e12492afd85392d3c8d850',310083000,NULL,NULL,'0d6d774dce93e94e870835005b0e8b04f010fb25158aa69a0fa0321d1577e987','1986d453cc232f931bc7cf3662fafae5a2567c8c6d9a2e9c3596c641b85e1259','4a864a2fc8e9714a81c3a060cdffaa2e7976f1eb7156949b1ce7e35ed58ea904');
INSERT INTO blocks VALUES(310084,'1e0972523e80306441b9f4157f171716199f1428db2e818a7f7817ccdc8859e3',310084000,NULL,NULL,'9dbd171e3606b1662f6b576339b1e9aaa3da8a9f8a246bab905af255add4a762','c0b8cd7252deb122de7486d3ace7bfea38a93c14d86f49f8e7844944ffed92e8','c9d465e2902646a43da0abf19e3411d097aea41f318fb06159d40acfcbd971ef');
INSERT INTO blocks VALUES(310085,'c5b6e9581831e3bc5848cd7630c499bca26d9ece5156d36579bdb72d54817e34',310085000,NULL,NULL,'db67b5dc6b0c0ddec22d0e716b72aa8cb6fa9702316f2a8e12659ee229094c16','1fb9951102d88d3b33a1a83b1218405bd9930064c9ffb7beed79968a7b365c94','91a7072bba9e0c545142f28eaad104b71b2aca625a9bb7d5262bd842785da90f');
INSERT INTO blocks VALUES(310086,'080c1dc55a4ecf4824cf9840602498cfc35b5f84099f50b71b45cb63834c7a78',310086000,NULL,NULL,'7cf70b5298dbb36efbec2fb880b76e2514e3bad9d5200875fa3eb3ceb7719ee8','b084ec5819661331926cead128d40617aca9f3952f9723dd6696ce16e455e6e4','39249e91bb44aa00288395fb023800d6dbabb23b1965c66c97ba8d6b7edb18ac');
INSERT INTO blocks VALUES(310087,'4ec8cb1c38b22904e8087a034a6406b896eff4dd28e7620601c6bddf82e2738c',310087000,NULL,NULL,'27106f400fe1ee93bde42f3bf3cf39737fb856bbf0df3f90fe0838cf7d38798c','2c0e919b220cee13d3c5c3c09e3a1775ce2130f1ffc7b06edc175524cd2a1d31','e83b501dba36bdc5b85ad4e2f165e12862f2c67cdb6da132f6806d426c3d751e');
INSERT INTO blocks VALUES(310088,'e945c815c433cbddd0bf8e66c5c23b51072483492acda98f5c2c201020a8c5b3',310088000,NULL,NULL,'28c9833eded6d68967f206e5884616f83bb9ad16b9d7a507031b96480aecc799','9c4e75c7d7b6005f47dbe7f1369734893131a22427b6cc8666f6960ee8fd309e','47ed9b3d8263a64c27435b72f8e837e8f624526a0aea75a736376603d1aaeb64');
INSERT INTO blocks VALUES(310089,'0382437f895ef3e7e38bf025fd4f606fd44d4bbd6aea71dbdc4ed11a7cd46f33',310089000,NULL,NULL,'cdac6435934ea6e67a311495325c85237158ef30c009ea44c562c2127d79e696','71ae5cda12526bacf81afb13e31246e24034ab327e3a425b04a8bf6885b4cac1','2784d42f3a56dbffb1a8fd27857da3a3a8260d9e82f7e0a72ee7fe266e333092');
INSERT INTO blocks VALUES(310090,'b756db71dc037b5a4582de354a3347371267d31ebda453e152f0a13bb2fae969',310090000,NULL,NULL,'cb33e420348e7969a2310445a6c17c79e647d3c6f3106d4fd0c0a1249e11ed6f','3340786671adc21aeb999d46af84798ee78071e9826b17fd6cd338618dd92c22','b68425eb030be1cb0b45be686d5d234ba3c3d4ba89eb6296770323e14fd314b2');
INSERT INTO blocks VALUES(310091,'734a9aa485f36399d5efb74f3b9c47f8b5f6fd68c9967f134b14cfe7e2d7583c',310091000,NULL,NULL,'dda2531cf7db78a3f27c1ce70189b3f6efb69ddd24b61639f9deff42566bba2a','61511a6c9938c9c08b93711362f05df217eeb500a273443aef4930f61b4f9066','25c23d01d5eacbd0a1fcb1adb9dd9268b05616b05941520f8f5bf7cbb31c0def');
INSERT INTO blocks VALUES(310092,'56386beb65f9228740d4ad43a1c575645f6daf59e0dd9f22551c59215b5e8c3d',310092000,NULL,NULL,'9ca7d9e1da0c6e4465d9e1c76990b6c48e62ee3a0b3b83189dc7a0f2c03a3006','abba408a80453c0aa30925f656e24421470832be4009986230cdd7ae623b01d7','134ff80f965468496e60c1907521413888e1a20c7b8444dd918df92024b30a3f');
INSERT INTO blocks VALUES(310093,'a74a2425f2f4be24bb5f715173e6756649e1cbf1b064aeb1ef60e0b94b418ddc',310093000,NULL,NULL,'c6fc005e874909cf0393ac1bee7267f66cc5355c549d8657234a0ed6b429c869','5de2329b5e949bb861d13ae6d74e0d738700b7783da277910e1ecdcd09c94599','10ed96e6427270fc13478c38f1f84caf2b56b6845f98d0597e800a5f57d2ce24');
INSERT INTO blocks VALUES(310094,'2a8f976f20c4e89ff01071915ac96ee35192d54df3a246bf61fd4a0cccfb5b23',310094000,NULL,NULL,'14dacaec0b37ca20f271e500d0ec1837a63006eb464728c067107738ad3167c6','aefde62be624e2faacf706e0613ff800425f911ff1ff675423b440d9a87a9111','2fb4636b18fbf71d13167551ad5303fac7605798d2b5bd987da041774308f56f');
INSERT INTO blocks VALUES(310095,'bed0fa40c9981223fb40b3be8124ca619edc9dd34d0c907369477ea92e5d2cd2',310095000,NULL,NULL,'05bd680c082185147e83785e7464d8890908d1550359b4fac79018b510475e01','fd1c6bbafbe273c57962ecc2121682b5dafa031db4e8e22aae95e63829388dad','8f6e998a581e000d5e572a5afa612a5f24f3d5df5ada35e61cc51e3cfba8228c');
INSERT INTO blocks VALUES(310096,'306aeec3db435fabffdf88c2f26ee83caa4c2426375a33daa2be041dbd27ea2f',310096000,NULL,NULL,'b50805d750ebd26f8dbced919948118f1f97ce7d117aa1760e7a3c4895f51e13','3ed172d143d39f6f7b141331952bf500d9f22874861dcd21b3478b35e908036f','a4bd5f8f0186c97519429674953a57d57debcb7c9ddf5c824769dcfdf459c44b');
INSERT INTO blocks VALUES(310097,'13e8e16e67c7cdcc80d477491e554b43744f90e8e1a9728439a11fab42cefadf',310097000,NULL,NULL,'dde96405c241e1d57334670e4eff7ed8db92056e6867cae10475a9bc30ba4619','62cb23788f3bd590c406c9cd24746e0c4730893c6ca45d0c675771f02344d9a8','76188410f7e04994f989d6cb44ca76cbdd9d24dea380d5642c997cd2437667d2');
INSERT INTO blocks VALUES(310098,'ca5bca4b5ec4fa6183e05176abe921cff884c4e20910fab55b603cef48dc3bca',310098000,NULL,NULL,'613d78fbabba246a4d1cd9d50317e732795a59812df8395472347e15cec1ee9b','bb76b59cee044c934188f8068545e94e8d7e2b934f10f9a9b990e5f71eb7ad8b','a05b6ae5266bb5cae48a57691a5cf1e188936093a1c8d5b6dd71d2c9c4439ce2');
INSERT INTO blocks VALUES(310099,'3c4c2279cd7de0add5ec469648a845875495a7d54ebfb5b012dcc5a197b7992a',310099000,NULL,NULL,'e535ca5960d2ce7508bd2157dd0cac3ea1f9ab14532a40884d522b4bba0d4979','bc2f014603b7cf873d046760441ca9b2191a3644bf3e5d967fdd2d325718427d','6dbfb491d824c8706cf13588569ead3b21c451db9b47c70ef2377c6fc232a047');
INSERT INTO blocks VALUES(310100,'96925c05b3c7c80c716f5bef68d161c71d044252c766ca0e3f17f255764242cb',310100000,NULL,NULL,'970865291b7a6d8173d6ad2ae97335cb2e89d80cbbb7a79bb2328cf6c67fa6cd','3bef6dfebfa695f9e8966296a3866b44afe656af6d031905b0ca9fcd4b0945b2','da9ccab09eb11ad5931b171b4ec0132d1309f137136a3134c35ef9f4a33f039d');
INSERT INTO blocks VALUES(310101,'369472409995ca1a2ebecbad6bf9dab38c378ab1e67e1bdf13d4ce1346731cd6',310101000,NULL,NULL,'0741e57ad88cdada65134c9f131ff5bfd9498cb054378d829e34715e8db2aa6d','941ec385ee3a091e8a18d3955d8a54891df6cdad73051f1e5fdf4525f26ec687','bddb23ad858a7b4de7690d3a57c9e87c3058d9e97caac9f0fe954ff8b6c9f7d7');
-- Triggers and indices on  blocks
CREATE INDEX block_index_idx ON blocks (block_index);
CREATE INDEX index_hash_idx ON blocks (block_index, block_hash);

-- Table  broadcasts
DROP TABLE IF EXISTS broadcasts;
CREATE TABLE broadcasts(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      timestamp INTEGER,
                      value REAL,
                      fee_fraction_int INTEGER,
                      text TEXT,
                      locked BOOL,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
INSERT INTO broadcasts VALUES(12,'1afa4fa28e1ef63b2b67c288e078cfeb109a2b236558ab5544eedc7f171e0a84',310011,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',1388000000,100.0,99999999,'Unit Test',0,'valid');
INSERT INTO broadcasts VALUES(19,'065de641fd87c0b3ef893130ef4a3dca7643b7a35f6d18c721f34a7a36a5992f',310018,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',1388000050,99.86166,5000000,'Unit Test',0,'valid');
INSERT INTO broadcasts VALUES(20,'7cc015005c559686a8e10294015ca1773c0bcd9f4d7d9768deb4bb94cdd4a69e',310019,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',1388000101,100.343,5000000,'Unit Test',0,'valid');
INSERT INTO broadcasts VALUES(21,'0899b8bccef3403252fd7d37ec550eea3350845dca098368b84bf4c3c48d3fc9',310020,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',1388000201,2.0,5000000,'Unit Test',0,'valid');
-- Triggers and indices on  broadcasts
CREATE TRIGGER _broadcasts_delete BEFORE DELETE ON broadcasts BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO broadcasts(rowid,tx_index,tx_hash,block_index,source,timestamp,value,fee_fraction_int,text,locked,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.timestamp)||','||quote(old.value)||','||quote(old.fee_fraction_int)||','||quote(old.text)||','||quote(old.locked)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _broadcasts_insert AFTER INSERT ON broadcasts BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM broadcasts WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _broadcasts_update AFTER UPDATE ON broadcasts BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE broadcasts SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',timestamp='||quote(old.timestamp)||',value='||quote(old.value)||',fee_fraction_int='||quote(old.fee_fraction_int)||',text='||quote(old.text)||',locked='||quote(old.locked)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX status_source_idx ON broadcasts (status, source);
CREATE INDEX status_source_index_idx ON broadcasts (status, source, tx_index);
CREATE INDEX timestamp_idx ON broadcasts (timestamp);

-- Table  btcpays
DROP TABLE IF EXISTS btcpays;
CREATE TABLE btcpays(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      destination TEXT,
                      btc_amount INTEGER,
                      order_match_id TEXT,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
INSERT INTO btcpays VALUES(5,'843c5df8f979db230ba61f26ad1342ed5803adeba7333b019b8a96ac6703f099',310004,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',50000000,'6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59_36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c','valid');
-- Triggers and indices on  btcpays
CREATE TRIGGER _btcpays_delete BEFORE DELETE ON btcpays BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO btcpays(rowid,tx_index,tx_hash,block_index,source,destination,btc_amount,order_match_id,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.destination)||','||quote(old.btc_amount)||','||quote(old.order_match_id)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _btcpays_insert AFTER INSERT ON btcpays BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM btcpays WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _btcpays_update AFTER UPDATE ON btcpays BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE btcpays SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',destination='||quote(old.destination)||',btc_amount='||quote(old.btc_amount)||',order_match_id='||quote(old.order_match_id)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;

-- Table  burns
DROP TABLE IF EXISTS burns;
CREATE TABLE burns(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      burned INTEGER,
                      earned INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
INSERT INTO burns VALUES(1,'6dc5b0a33d4d4297e0f5cc2d23ae307951d32aab2d86b7fa147b385219f3a597',310000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',62000000,93000000000,'valid');
INSERT INTO burns VALUES(23,'c3f73d02e630cb2824f044e6d91f47b1ce351feff0339ea7b85652d24d8ff6bc',310022,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',38000000,56999887262,'valid');
-- Triggers and indices on  burns
CREATE TRIGGER _burns_delete BEFORE DELETE ON burns BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO burns(rowid,tx_index,tx_hash,block_index,source,burned,earned,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.burned)||','||quote(old.earned)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _burns_insert AFTER INSERT ON burns BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM burns WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _burns_update AFTER UPDATE ON burns BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE burns SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',burned='||quote(old.burned)||',earned='||quote(old.earned)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;

-- Table  cancels
DROP TABLE IF EXISTS cancels;
CREATE TABLE cancels(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      offer_hash TEXT,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
-- Triggers and indices on  cancels
CREATE TRIGGER _cancels_delete BEFORE DELETE ON cancels BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO cancels(rowid,tx_index,tx_hash,block_index,source,offer_hash,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.offer_hash)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _cancels_insert AFTER INSERT ON cancels BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM cancels WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _cancels_update AFTER UPDATE ON cancels BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE cancels SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',offer_hash='||quote(old.offer_hash)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX cancels_block_index_idx ON cancels (block_index);

-- Table  credits
DROP TABLE IF EXISTS credits;
CREATE TABLE credits(
                      block_index INTEGER,
                      address TEXT,
                      asset TEXT,
                      quantity INTEGER,
                      calling_function TEXT,
                      event TEXT,
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index));
INSERT INTO credits VALUES(310000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',93000000000,'burn','6dc5b0a33d4d4297e0f5cc2d23ae307951d32aab2d86b7fa147b385219f3a597');
INSERT INTO credits VALUES(310001,'mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','XCP',50000000,'send','3b273ba342ed8bd4ccd2ae28d3df7754768a6c65ec1cee4a6e84b4b4bdec8d8c');
INSERT INTO credits VALUES(310004,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',100000000,'btcpay','843c5df8f979db230ba61f26ad1342ed5803adeba7333b019b8a96ac6703f099');
INSERT INTO credits VALUES(310005,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBB',1000000000,'issuance','5d951d44d034cb6fd5dc5c98cd877c63f55c1ae108d335b6b6d991d072856adf');
INSERT INTO credits VALUES(310006,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBC',100000,'issuance','41c590d8bc8a0bd0e436c4c50e14c2ce86df3cd3450336bff5d01cdf7f122753');
INSERT INTO credits VALUES(310007,'mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','BBBB',4000000,'send','5836fb23c2bb94eeb4b71cb8e3c622c6d943b3e4ed3aebee42d240445e615db8');
INSERT INTO credits VALUES(310008,'mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','BBBC',526,'send','843e6f7712b7847099502bda8a4bd7127c17a2799290b91ef1584a6bfe069412');
INSERT INTO credits VALUES(310009,'mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','XCP',24,'dividend','42ae2fd7f3a18f84334bc37aa88283e79d6bff0b234dbf97e788695957d75518');
INSERT INTO credits VALUES(310010,'mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','XCP',420800,'dividend','201123e1ddbc4dab954fed0043a29fca770a9bd4268714354bb7991f01133c10');
INSERT INTO credits VALUES(310013,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',4250000,'filled','e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42');
INSERT INTO credits VALUES(310014,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',5000000,'cancel order','36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c');
INSERT INTO credits VALUES(310015,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',0,'filled','a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8');
INSERT INTO credits VALUES(310015,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',0,'filled','a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8');
INSERT INTO credits VALUES(310017,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',0,'filled','72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207');
INSERT INTO credits VALUES(310017,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',0,'filled','72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207');
INSERT INTO credits VALUES(310018,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',59137500,'bet settled: liquidated for bear','065de641fd87c0b3ef893130ef4a3dca7643b7a35f6d18c721f34a7a36a5992f');
INSERT INTO credits VALUES(310018,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',3112500,'feed fee','065de641fd87c0b3ef893130ef4a3dca7643b7a35f6d18c721f34a7a36a5992f');
INSERT INTO credits VALUES(310019,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',159300000,'bet settled','7cc015005c559686a8e10294015ca1773c0bcd9f4d7d9768deb4bb94cdd4a69e');
INSERT INTO credits VALUES(310019,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',315700000,'bet settled','7cc015005c559686a8e10294015ca1773c0bcd9f4d7d9768deb4bb94cdd4a69e');
INSERT INTO credits VALUES(310019,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',25000000,'feed fee','7cc015005c559686a8e10294015ca1773c0bcd9f4d7d9768deb4bb94cdd4a69e');
INSERT INTO credits VALUES(310020,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',1330000000,'bet settled: for notequal','0899b8bccef3403252fd7d37ec550eea3350845dca098368b84bf4c3c48d3fc9');
INSERT INTO credits VALUES(310020,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',70000000,'feed fee','0899b8bccef3403252fd7d37ec550eea3350845dca098368b84bf4c3c48d3fc9');
INSERT INTO credits VALUES(310022,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',56999887262,'burn','c3f73d02e630cb2824f044e6d91f47b1ce351feff0339ea7b85652d24d8ff6bc');
INSERT INTO credits VALUES(310023,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',8500000,'recredit wager remaining','7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81');
INSERT INTO credits VALUES(310023,'mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','BBBC',10000,'send','58b89d056b539d2cf9ddac4518ccca6744495127e0ce893eb71da2599cbf85ab');
INSERT INTO credits VALUES(310032,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBB',50000000,'cancel order','eb5953f4e1dec30f0bf4741cb2044c11b6e1c3be20fef2111461f69d989b852a');
-- Triggers and indices on  credits
CREATE TRIGGER _credits_delete BEFORE DELETE ON credits BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO credits(rowid,block_index,address,asset,quantity,calling_function,event) VALUES('||old.rowid||','||quote(old.block_index)||','||quote(old.address)||','||quote(old.asset)||','||quote(old.quantity)||','||quote(old.calling_function)||','||quote(old.event)||')');
                            END;
CREATE TRIGGER _credits_insert AFTER INSERT ON credits BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM credits WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _credits_update AFTER UPDATE ON credits BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE credits SET block_index='||quote(old.block_index)||',address='||quote(old.address)||',asset='||quote(old.asset)||',quantity='||quote(old.quantity)||',calling_function='||quote(old.calling_function)||',event='||quote(old.event)||' WHERE rowid='||old.rowid);
                            END;

-- Table  debits
DROP TABLE IF EXISTS debits;
CREATE TABLE debits(
                      block_index INTEGER,
                      address TEXT,
                      asset TEXT,
                      quantity INTEGER,
                      action TEXT,
                      event TEXT,
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index));
INSERT INTO debits VALUES(310001,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',50000000,'send','3b273ba342ed8bd4ccd2ae28d3df7754768a6c65ec1cee4a6e84b4b4bdec8d8c');
INSERT INTO debits VALUES(310003,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',105000000,'open order','36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c');
INSERT INTO debits VALUES(310005,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',50000000,'issuance fee','5d951d44d034cb6fd5dc5c98cd877c63f55c1ae108d335b6b6d991d072856adf');
INSERT INTO debits VALUES(310006,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',50000000,'issuance fee','41c590d8bc8a0bd0e436c4c50e14c2ce86df3cd3450336bff5d01cdf7f122753');
INSERT INTO debits VALUES(310007,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBB',4000000,'send','5836fb23c2bb94eeb4b71cb8e3c622c6d943b3e4ed3aebee42d240445e615db8');
INSERT INTO debits VALUES(310008,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBC',526,'send','843e6f7712b7847099502bda8a4bd7127c17a2799290b91ef1584a6bfe069412');
INSERT INTO debits VALUES(310009,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',24,'dividend','42ae2fd7f3a18f84334bc37aa88283e79d6bff0b234dbf97e788695957d75518');
INSERT INTO debits VALUES(310009,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',20000,'dividend fee','42ae2fd7f3a18f84334bc37aa88283e79d6bff0b234dbf97e788695957d75518');
INSERT INTO debits VALUES(310010,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',420800,'dividend','201123e1ddbc4dab954fed0043a29fca770a9bd4268714354bb7991f01133c10');
INSERT INTO debits VALUES(310010,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',20000,'dividend fee','201123e1ddbc4dab954fed0043a29fca770a9bd4268714354bb7991f01133c10');
INSERT INTO debits VALUES(310012,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',50000000,'bet','7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81');
INSERT INTO debits VALUES(310013,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',25000000,'bet','e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42');
INSERT INTO debits VALUES(310014,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',150000000,'bet','3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a');
INSERT INTO debits VALUES(310015,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',350000000,'bet','a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8');
INSERT INTO debits VALUES(310016,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',750000000,'bet','194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5');
INSERT INTO debits VALUES(310017,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',650000000,'bet','72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207');
INSERT INTO debits VALUES(310021,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBB',50000000,'open order','eb5953f4e1dec30f0bf4741cb2044c11b6e1c3be20fef2111461f69d989b852a');
INSERT INTO debits VALUES(310023,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBC',10000,'send','58b89d056b539d2cf9ddac4518ccca6744495127e0ce893eb71da2599cbf85ab');
-- Triggers and indices on  debits
CREATE TRIGGER _debits_delete BEFORE DELETE ON debits BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO debits(rowid,block_index,address,asset,quantity,action,event) VALUES('||old.rowid||','||quote(old.block_index)||','||quote(old.address)||','||quote(old.asset)||','||quote(old.quantity)||','||quote(old.action)||','||quote(old.event)||')');
                            END;
CREATE TRIGGER _debits_insert AFTER INSERT ON debits BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM debits WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _debits_update AFTER UPDATE ON debits BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE debits SET block_index='||quote(old.block_index)||',address='||quote(old.address)||',asset='||quote(old.asset)||',quantity='||quote(old.quantity)||',action='||quote(old.action)||',event='||quote(old.event)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX address_idx ON debits (address);
CREATE INDEX asset_idx ON debits (asset);

-- Table  destructions
DROP TABLE IF EXISTS destructions;
CREATE TABLE destructions(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      asset INTEGER,
                      quantity INTEGER,
                      tag TEXT,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
-- Triggers and indices on  destructions
CREATE TRIGGER _destructions_delete BEFORE DELETE ON destructions BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO destructions(rowid,tx_index,tx_hash,block_index,source,asset,quantity,tag,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.asset)||','||quote(old.quantity)||','||quote(old.tag)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _destructions_insert AFTER INSERT ON destructions BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM destructions WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _destructions_update AFTER UPDATE ON destructions BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE destructions SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',asset='||quote(old.asset)||',quantity='||quote(old.quantity)||',tag='||quote(old.tag)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX status_idx ON destructions (status);

-- Table  dispenser_refills
DROP TABLE IF EXISTS dispenser_refills;
CREATE TABLE dispenser_refills(
                      tx_index INTEGER,
                      tx_hash TEXT,
                      block_index INTEGER,
                      source TEXT,
                      destination TEXT,
                      asset TEXT,
                      dispense_quantity INTEGER,
                      dispenser_tx_hash TEXT,
                      PRIMARY KEY (tx_index, tx_hash, source, destination),
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
-- Triggers and indices on  dispenser_refills
CREATE TRIGGER _dispenser_refills_delete BEFORE DELETE ON dispenser_refills BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO dispenser_refills(rowid,tx_index,tx_hash,block_index,source,destination,asset,dispense_quantity,dispenser_tx_hash) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.destination)||','||quote(old.asset)||','||quote(old.dispense_quantity)||','||quote(old.dispenser_tx_hash)||')');
                            END;
CREATE TRIGGER _dispenser_refills_insert AFTER INSERT ON dispenser_refills BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM dispenser_refills WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _dispenser_refills_update AFTER UPDATE ON dispenser_refills BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE dispenser_refills SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',destination='||quote(old.destination)||',asset='||quote(old.asset)||',dispense_quantity='||quote(old.dispense_quantity)||',dispenser_tx_hash='||quote(old.dispenser_tx_hash)||' WHERE rowid='||old.rowid);
                            END;

-- Table  dispensers
DROP TABLE IF EXISTS dispensers;
CREATE TABLE dispensers(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      asset TEXT,
                      give_quantity INTEGER,
                      escrow_quantity INTEGER,
                      satoshirate INTEGER,
                      status INTEGER,
                      give_remaining INTEGER, oracle_address TEXT, last_status_tx_hash TEXT, origin TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
-- Triggers and indices on  dispensers
CREATE TRIGGER _dispensers_delete BEFORE DELETE ON dispensers BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO dispensers(rowid,tx_index,tx_hash,block_index,source,asset,give_quantity,escrow_quantity,satoshirate,status,give_remaining,oracle_address,last_status_tx_hash,origin) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.asset)||','||quote(old.give_quantity)||','||quote(old.escrow_quantity)||','||quote(old.satoshirate)||','||quote(old.status)||','||quote(old.give_remaining)||','||quote(old.oracle_address)||','||quote(old.last_status_tx_hash)||','||quote(old.origin)||')');
                            END;
CREATE TRIGGER _dispensers_insert AFTER INSERT ON dispensers BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM dispensers WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _dispensers_update AFTER UPDATE ON dispensers BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE dispensers SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',asset='||quote(old.asset)||',give_quantity='||quote(old.give_quantity)||',escrow_quantity='||quote(old.escrow_quantity)||',satoshirate='||quote(old.satoshirate)||',status='||quote(old.status)||',give_remaining='||quote(old.give_remaining)||',oracle_address='||quote(old.oracle_address)||',last_status_tx_hash='||quote(old.last_status_tx_hash)||',origin='||quote(old.origin)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX dispensers_asset_idx ON dispensers (asset);
CREATE INDEX dispensers_source_idx ON dispensers (source);

-- Table  dispenses
DROP TABLE IF EXISTS dispenses;
CREATE TABLE dispenses(
                      tx_index INTEGER,
                      dispense_index INTEGER,
                      tx_hash TEXT,
                      block_index INTEGER,
                      source TEXT,
                      destination TEXT,
                      asset TEXT,
                      dispense_quantity INTEGER,
                      dispenser_tx_hash TEXT,
                      PRIMARY KEY (tx_index, dispense_index, source, destination),
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
-- Triggers and indices on  dispenses
CREATE TRIGGER _dispenses_delete BEFORE DELETE ON dispenses BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO dispenses(rowid,tx_index,dispense_index,tx_hash,block_index,source,destination,asset,dispense_quantity,dispenser_tx_hash) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.dispense_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.destination)||','||quote(old.asset)||','||quote(old.dispense_quantity)||','||quote(old.dispenser_tx_hash)||')');
                            END;
CREATE TRIGGER _dispenses_insert AFTER INSERT ON dispenses BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM dispenses WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _dispenses_update AFTER UPDATE ON dispenses BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE dispenses SET tx_index='||quote(old.tx_index)||',dispense_index='||quote(old.dispense_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',destination='||quote(old.destination)||',asset='||quote(old.asset)||',dispense_quantity='||quote(old.dispense_quantity)||',dispenser_tx_hash='||quote(old.dispenser_tx_hash)||' WHERE rowid='||old.rowid);
                            END;

-- Table  dividends
DROP TABLE IF EXISTS dividends;
CREATE TABLE dividends(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      asset TEXT,
                      dividend_asset TEXT,
                      quantity_per_unit INTEGER,
                      fee_paid INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
INSERT INTO dividends VALUES(10,'42ae2fd7f3a18f84334bc37aa88283e79d6bff0b234dbf97e788695957d75518',310009,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBB','XCP',600,20000,'valid');
INSERT INTO dividends VALUES(11,'201123e1ddbc4dab954fed0043a29fca770a9bd4268714354bb7991f01133c10',310010,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBC','XCP',800,20000,'valid');
-- Triggers and indices on  dividends
CREATE TRIGGER _dividends_delete BEFORE DELETE ON dividends BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO dividends(rowid,tx_index,tx_hash,block_index,source,asset,dividend_asset,quantity_per_unit,fee_paid,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.asset)||','||quote(old.dividend_asset)||','||quote(old.quantity_per_unit)||','||quote(old.fee_paid)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _dividends_insert AFTER INSERT ON dividends BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM dividends WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _dividends_update AFTER UPDATE ON dividends BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE dividends SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',asset='||quote(old.asset)||',dividend_asset='||quote(old.dividend_asset)||',quantity_per_unit='||quote(old.quantity_per_unit)||',fee_paid='||quote(old.fee_paid)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;

-- Table  issuances
DROP TABLE IF EXISTS issuances;
CREATE TABLE "issuances"(
                              tx_index INTEGER,
                              tx_hash TEXT,
                              msg_index INTEGER DEFAULT 0,
                              block_index INTEGER,
                              asset TEXT,
                              quantity INTEGER,
                              divisible BOOL,
                              source TEXT,
                              issuer TEXT,
                              transfer BOOL,
                              callable BOOL,
                              call_date INTEGER,
                              call_price REAL,
                              description TEXT,
                              fee_paid INTEGER,
                              locked BOOL,
                              status TEXT,
                              asset_longname TEXT,
                              reset BOOL,
                              PRIMARY KEY (tx_index, msg_index),
                              FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                              UNIQUE (tx_hash, msg_index));
INSERT INTO issuances VALUES(6,'5d951d44d034cb6fd5dc5c98cd877c63f55c1ae108d335b6b6d991d072856adf',0,310005,'BBBB',1000000000,1,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',0,0,0,0.0,'',50000000,0,'valid',NULL,0);
INSERT INTO issuances VALUES(7,'41c590d8bc8a0bd0e436c4c50e14c2ce86df3cd3450336bff5d01cdf7f122753',0,310006,'BBBC',100000,0,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',0,0,0,0.0,'',50000000,0,'valid',NULL,0);
-- Triggers and indices on  issuances
CREATE TRIGGER _issuances_delete BEFORE DELETE ON issuances BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO issuances(rowid,tx_index,tx_hash,msg_index,block_index,asset,quantity,divisible,source,issuer,transfer,callable,call_date,call_price,description,fee_paid,locked,status,asset_longname,reset) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.msg_index)||','||quote(old.block_index)||','||quote(old.asset)||','||quote(old.quantity)||','||quote(old.divisible)||','||quote(old.source)||','||quote(old.issuer)||','||quote(old.transfer)||','||quote(old.callable)||','||quote(old.call_date)||','||quote(old.call_price)||','||quote(old.description)||','||quote(old.fee_paid)||','||quote(old.locked)||','||quote(old.status)||','||quote(old.asset_longname)||','||quote(old.reset)||')');
                            END;
CREATE TRIGGER _issuances_insert AFTER INSERT ON issuances BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM issuances WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _issuances_update AFTER UPDATE ON issuances BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE issuances SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',msg_index='||quote(old.msg_index)||',block_index='||quote(old.block_index)||',asset='||quote(old.asset)||',quantity='||quote(old.quantity)||',divisible='||quote(old.divisible)||',source='||quote(old.source)||',issuer='||quote(old.issuer)||',transfer='||quote(old.transfer)||',callable='||quote(old.callable)||',call_date='||quote(old.call_date)||',call_price='||quote(old.call_price)||',description='||quote(old.description)||',fee_paid='||quote(old.fee_paid)||',locked='||quote(old.locked)||',status='||quote(old.status)||',asset_longname='||quote(old.asset_longname)||',reset='||quote(old.reset)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX valid_asset_idx ON issuances (asset, status);

-- Table  mempool
DROP TABLE IF EXISTS mempool;
CREATE TABLE mempool(
                      tx_hash TEXT,
                      command TEXT,
                      category TEXT,
                      bindings TEXT,
                      timestamp INTEGER);

-- Table  messages
DROP TABLE IF EXISTS messages;
CREATE TABLE messages(
                      message_index INTEGER PRIMARY KEY,
                      block_index INTEGER,
                      command TEXT,
                      category TEXT,
                      bindings TEXT,
                      timestamp INTEGER);
INSERT INTO messages VALUES(0,309999,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(1,310000,'insert','replace','[''block_index'', ''first_undo_index'']',0);
INSERT INTO messages VALUES(2,310000,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(3,310000,'insert','burns','[''block_index'', ''burned'', ''earned'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(4,310001,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(5,310001,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(6,310001,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(7,310001,'insert','sends','[''asset'', ''block_index'', ''destination'', ''quantity'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(8,310002,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(9,310002,'insert','orders','[''block_index'', ''expiration'', ''expire_index'', ''fee_provided'', ''fee_provided_remaining'', ''fee_required'', ''fee_required_remaining'', ''get_asset'', ''get_quantity'', ''get_remaining'', ''give_asset'', ''give_quantity'', ''give_remaining'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(10,310003,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(11,310003,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(12,310003,'insert','orders','[''block_index'', ''expiration'', ''expire_index'', ''fee_provided'', ''fee_provided_remaining'', ''fee_required'', ''fee_required_remaining'', ''get_asset'', ''get_quantity'', ''get_remaining'', ''give_asset'', ''give_quantity'', ''give_remaining'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(13,310003,'update','orders','[''fee_provided_remaining'', ''fee_required_remaining'', ''get_remaining'', ''give_remaining'', ''status'', ''tx_hash'']',0);
INSERT INTO messages VALUES(14,310003,'update','orders','[''fee_provided_remaining'', ''fee_required_remaining'', ''get_remaining'', ''give_remaining'', ''status'', ''tx_hash'']',0);
INSERT INTO messages VALUES(15,310003,'insert','order_matches','[''backward_asset'', ''backward_quantity'', ''block_index'', ''fee_paid'', ''forward_asset'', ''forward_quantity'', ''id'', ''match_expire_index'', ''status'', ''tx0_address'', ''tx0_block_index'', ''tx0_expiration'', ''tx0_hash'', ''tx0_index'', ''tx1_address'', ''tx1_block_index'', ''tx1_expiration'', ''tx1_hash'', ''tx1_index'']',0);
INSERT INTO messages VALUES(16,310004,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(17,310004,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(18,310004,'update','order_matches','[''order_match_id'', ''status'']',0);
INSERT INTO messages VALUES(19,310004,'insert','btcpays','[''block_index'', ''btc_amount'', ''destination'', ''order_match_id'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(20,310005,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(21,310005,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(22,310005,'insert','issuances','[''asset'', ''asset_longname'', ''block_index'', ''call_date'', ''call_price'', ''callable'', ''description'', ''divisible'', ''fee_paid'', ''issuer'', ''locked'', ''quantity'', ''reset'', ''source'', ''status'', ''transfer'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(23,310005,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(24,310006,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(25,310006,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(26,310006,'insert','issuances','[''asset'', ''asset_longname'', ''block_index'', ''call_date'', ''call_price'', ''callable'', ''description'', ''divisible'', ''fee_paid'', ''issuer'', ''locked'', ''quantity'', ''reset'', ''source'', ''status'', ''transfer'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(27,310006,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(28,310007,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(29,310007,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(30,310007,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(31,310007,'insert','sends','[''asset'', ''block_index'', ''destination'', ''quantity'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(32,310008,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(33,310008,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(34,310008,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(35,310008,'insert','sends','[''asset'', ''block_index'', ''destination'', ''quantity'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(36,310009,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(37,310009,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(38,310009,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(39,310009,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(40,310009,'insert','dividends','[''asset'', ''block_index'', ''dividend_asset'', ''fee_paid'', ''quantity_per_unit'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(41,310010,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(42,310010,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(43,310010,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(44,310010,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(45,310010,'insert','dividends','[''asset'', ''block_index'', ''dividend_asset'', ''fee_paid'', ''quantity_per_unit'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(46,310011,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(47,310011,'insert','broadcasts','[''block_index'', ''fee_fraction_int'', ''locked'', ''source'', ''status'', ''text'', ''timestamp'', ''tx_hash'', ''tx_index'', ''value'']',0);
INSERT INTO messages VALUES(48,310012,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(49,310012,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(50,310012,'insert','bets','[''bet_type'', ''block_index'', ''counterwager_quantity'', ''counterwager_remaining'', ''deadline'', ''expiration'', ''expire_index'', ''fee_fraction_int'', ''feed_address'', ''leverage'', ''source'', ''status'', ''target_value'', ''tx_hash'', ''tx_index'', ''wager_quantity'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(51,310013,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(52,310013,'update','orders','[''status'', ''tx_hash'']',0);
INSERT INTO messages VALUES(53,310013,'insert','order_expirations','[''block_index'', ''order_hash'', ''order_index'', ''source'']',0);
INSERT INTO messages VALUES(54,310013,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(55,310013,'insert','bets','[''bet_type'', ''block_index'', ''counterwager_quantity'', ''counterwager_remaining'', ''deadline'', ''expiration'', ''expire_index'', ''fee_fraction_int'', ''feed_address'', ''leverage'', ''source'', ''status'', ''target_value'', ''tx_hash'', ''tx_index'', ''wager_quantity'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(56,310013,'update','bets','[''counterwager_remaining'', ''status'', ''tx_hash'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(57,310013,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(58,310013,'update','bets','[''counterwager_remaining'', ''status'', ''tx_hash'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(59,310013,'insert','bet_matches','[''backward_quantity'', ''block_index'', ''deadline'', ''fee_fraction_int'', ''feed_address'', ''forward_quantity'', ''id'', ''initial_value'', ''leverage'', ''match_expire_index'', ''status'', ''target_value'', ''tx0_address'', ''tx0_bet_type'', ''tx0_block_index'', ''tx0_expiration'', ''tx0_hash'', ''tx0_index'', ''tx1_address'', ''tx1_bet_type'', ''tx1_block_index'', ''tx1_expiration'', ''tx1_hash'', ''tx1_index'']',0);
INSERT INTO messages VALUES(60,310014,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(61,310014,'update','orders','[''status'', ''tx_hash'']',0);
INSERT INTO messages VALUES(62,310014,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(63,310014,'insert','order_expirations','[''block_index'', ''order_hash'', ''order_index'', ''source'']',0);
INSERT INTO messages VALUES(64,310014,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(65,310014,'insert','bets','[''bet_type'', ''block_index'', ''counterwager_quantity'', ''counterwager_remaining'', ''deadline'', ''expiration'', ''expire_index'', ''fee_fraction_int'', ''feed_address'', ''leverage'', ''source'', ''status'', ''target_value'', ''tx_hash'', ''tx_index'', ''wager_quantity'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(66,310015,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(67,310015,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(68,310015,'insert','bets','[''bet_type'', ''block_index'', ''counterwager_quantity'', ''counterwager_remaining'', ''deadline'', ''expiration'', ''expire_index'', ''fee_fraction_int'', ''feed_address'', ''leverage'', ''source'', ''status'', ''target_value'', ''tx_hash'', ''tx_index'', ''wager_quantity'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(69,310015,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(70,310015,'update','bets','[''counterwager_remaining'', ''status'', ''tx_hash'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(71,310015,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(72,310015,'update','bets','[''counterwager_remaining'', ''status'', ''tx_hash'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(73,310015,'insert','bet_matches','[''backward_quantity'', ''block_index'', ''deadline'', ''fee_fraction_int'', ''feed_address'', ''forward_quantity'', ''id'', ''initial_value'', ''leverage'', ''match_expire_index'', ''status'', ''target_value'', ''tx0_address'', ''tx0_bet_type'', ''tx0_block_index'', ''tx0_expiration'', ''tx0_hash'', ''tx0_index'', ''tx1_address'', ''tx1_bet_type'', ''tx1_block_index'', ''tx1_expiration'', ''tx1_hash'', ''tx1_index'']',0);
INSERT INTO messages VALUES(74,310016,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(75,310016,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(76,310016,'insert','bets','[''bet_type'', ''block_index'', ''counterwager_quantity'', ''counterwager_remaining'', ''deadline'', ''expiration'', ''expire_index'', ''fee_fraction_int'', ''feed_address'', ''leverage'', ''source'', ''status'', ''target_value'', ''tx_hash'', ''tx_index'', ''wager_quantity'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(77,310017,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(78,310017,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(79,310017,'insert','bets','[''bet_type'', ''block_index'', ''counterwager_quantity'', ''counterwager_remaining'', ''deadline'', ''expiration'', ''expire_index'', ''fee_fraction_int'', ''feed_address'', ''leverage'', ''source'', ''status'', ''target_value'', ''tx_hash'', ''tx_index'', ''wager_quantity'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(80,310017,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(81,310017,'update','bets','[''counterwager_remaining'', ''status'', ''tx_hash'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(82,310017,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(83,310017,'update','bets','[''counterwager_remaining'', ''status'', ''tx_hash'', ''wager_remaining'']',0);
INSERT INTO messages VALUES(84,310017,'insert','bet_matches','[''backward_quantity'', ''block_index'', ''deadline'', ''fee_fraction_int'', ''feed_address'', ''forward_quantity'', ''id'', ''initial_value'', ''leverage'', ''match_expire_index'', ''status'', ''target_value'', ''tx0_address'', ''tx0_bet_type'', ''tx0_block_index'', ''tx0_expiration'', ''tx0_hash'', ''tx0_index'', ''tx1_address'', ''tx1_bet_type'', ''tx1_block_index'', ''tx1_expiration'', ''tx1_hash'', ''tx1_index'']',0);
INSERT INTO messages VALUES(85,310018,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(86,310018,'insert','broadcasts','[''block_index'', ''fee_fraction_int'', ''locked'', ''source'', ''status'', ''text'', ''timestamp'', ''tx_hash'', ''tx_index'', ''value'']',0);
INSERT INTO messages VALUES(87,310018,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(88,310018,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(89,310018,'insert','bet_match_resolutions','[''bear_credit'', ''bet_match_id'', ''bet_match_type_id'', ''block_index'', ''bull_credit'', ''escrow_less_fee'', ''fee'', ''settled'', ''winner'']',0);
INSERT INTO messages VALUES(90,310018,'update','bet_matches','[''bet_match_id'', ''status'']',0);
INSERT INTO messages VALUES(91,310019,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(92,310019,'insert','broadcasts','[''block_index'', ''fee_fraction_int'', ''locked'', ''source'', ''status'', ''text'', ''timestamp'', ''tx_hash'', ''tx_index'', ''value'']',0);
INSERT INTO messages VALUES(93,310019,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(94,310019,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(95,310019,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(96,310019,'insert','bet_match_resolutions','[''bear_credit'', ''bet_match_id'', ''bet_match_type_id'', ''block_index'', ''bull_credit'', ''escrow_less_fee'', ''fee'', ''settled'', ''winner'']',0);
INSERT INTO messages VALUES(97,310019,'update','bet_matches','[''bet_match_id'', ''status'']',0);
INSERT INTO messages VALUES(98,310020,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(99,310020,'insert','broadcasts','[''block_index'', ''fee_fraction_int'', ''locked'', ''source'', ''status'', ''text'', ''timestamp'', ''tx_hash'', ''tx_index'', ''value'']',0);
INSERT INTO messages VALUES(100,310020,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(101,310020,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(102,310020,'insert','bet_match_resolutions','[''bear_credit'', ''bet_match_id'', ''bet_match_type_id'', ''block_index'', ''bull_credit'', ''escrow_less_fee'', ''fee'', ''settled'', ''winner'']',0);
INSERT INTO messages VALUES(103,310020,'update','bet_matches','[''bet_match_id'', ''status'']',0);
INSERT INTO messages VALUES(104,310021,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(105,310021,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(106,310021,'insert','orders','[''block_index'', ''expiration'', ''expire_index'', ''fee_provided'', ''fee_provided_remaining'', ''fee_required'', ''fee_required_remaining'', ''get_asset'', ''get_quantity'', ''get_remaining'', ''give_asset'', ''give_quantity'', ''give_remaining'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(107,310022,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(108,310022,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(109,310022,'insert','burns','[''block_index'', ''burned'', ''earned'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(110,310023,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(111,310023,'update','bets','[''status'', ''tx_hash'']',0);
INSERT INTO messages VALUES(112,310023,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(113,310023,'insert','bet_expirations','[''bet_hash'', ''bet_index'', ''block_index'', ''source'']',0);
INSERT INTO messages VALUES(114,310023,'insert','debits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(115,310023,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(116,310023,'insert','sends','[''asset'', ''block_index'', ''destination'', ''quantity'', ''source'', ''status'', ''tx_hash'', ''tx_index'']',0);
INSERT INTO messages VALUES(117,310024,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(118,310025,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(119,310026,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(120,310027,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(121,310028,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(122,310029,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(123,310030,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(124,310031,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(125,310032,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(126,310032,'update','orders','[''status'', ''tx_hash'']',0);
INSERT INTO messages VALUES(127,310032,'insert','credits','[''action'', ''address'', ''asset'', ''block_index'', ''event'', ''quantity'']',0);
INSERT INTO messages VALUES(128,310032,'insert','order_expirations','[''block_index'', ''order_hash'', ''order_index'', ''source'']',0);
INSERT INTO messages VALUES(129,310033,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(130,310034,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(131,310035,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(132,310036,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(133,310037,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(134,310038,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(135,310039,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(136,310040,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(137,310041,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(138,310042,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(139,310043,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(140,310044,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(141,310045,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(142,310046,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(143,310047,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(144,310048,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(145,310049,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(146,310050,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(147,310051,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(148,310052,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(149,310053,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(150,310054,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(151,310055,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(152,310056,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(153,310057,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(154,310058,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(155,310059,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(156,310060,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(157,310061,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(158,310062,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(159,310063,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(160,310064,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(161,310065,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(162,310066,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(163,310067,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(164,310068,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(165,310069,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(166,310070,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(167,310071,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(168,310072,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(169,310073,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(170,310074,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(171,310075,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(172,310076,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(173,310077,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(174,310078,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(175,310079,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(176,310080,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(177,310081,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(178,310082,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(179,310083,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(180,310084,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(181,310085,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(182,310086,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(183,310087,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(184,310088,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(185,310089,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(186,310090,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(187,310091,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(188,310092,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(189,310093,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(190,310094,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(191,310095,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(192,310096,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(193,310097,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(194,310098,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(195,310099,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(196,310100,'insert','replace','[''block_index'']',0);
INSERT INTO messages VALUES(197,310101,'insert','replace','[''block_index'']',0);
-- Triggers and indices on  messages
CREATE INDEX block_index_message_index_idx ON messages (block_index, message_index);

-- Table  order_expirations
DROP TABLE IF EXISTS order_expirations;
CREATE TABLE order_expirations(
                      order_index INTEGER PRIMARY KEY,
                      order_hash TEXT UNIQUE,
                      source TEXT,
                      block_index INTEGER,
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index),
                      FOREIGN KEY (order_index, order_hash) REFERENCES orders(tx_index, tx_hash));
INSERT INTO order_expirations VALUES(3,'6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',310013);
INSERT INTO order_expirations VALUES(4,'36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',310014);
INSERT INTO order_expirations VALUES(22,'eb5953f4e1dec30f0bf4741cb2044c11b6e1c3be20fef2111461f69d989b852a','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',310032);
-- Triggers and indices on  order_expirations
CREATE TRIGGER _order_expirations_delete BEFORE DELETE ON order_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO order_expirations(rowid,order_index,order_hash,source,block_index) VALUES('||old.rowid||','||quote(old.order_index)||','||quote(old.order_hash)||','||quote(old.source)||','||quote(old.block_index)||')');
                            END;
CREATE TRIGGER _order_expirations_insert AFTER INSERT ON order_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM order_expirations WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _order_expirations_update AFTER UPDATE ON order_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE order_expirations SET order_index='||quote(old.order_index)||',order_hash='||quote(old.order_hash)||',source='||quote(old.source)||',block_index='||quote(old.block_index)||' WHERE rowid='||old.rowid);
                            END;

-- Table  order_match_expirations
DROP TABLE IF EXISTS order_match_expirations;
CREATE TABLE order_match_expirations(
                      order_match_id TEXT PRIMARY KEY,
                      tx0_address TEXT,
                      tx1_address TEXT,
                      block_index INTEGER,
                      FOREIGN KEY (order_match_id) REFERENCES order_matches(id),
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index));
-- Triggers and indices on  order_match_expirations
CREATE TRIGGER _order_match_expirations_delete BEFORE DELETE ON order_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO order_match_expirations(rowid,order_match_id,tx0_address,tx1_address,block_index) VALUES('||old.rowid||','||quote(old.order_match_id)||','||quote(old.tx0_address)||','||quote(old.tx1_address)||','||quote(old.block_index)||')');
                            END;
CREATE TRIGGER _order_match_expirations_insert AFTER INSERT ON order_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM order_match_expirations WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _order_match_expirations_update AFTER UPDATE ON order_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE order_match_expirations SET order_match_id='||quote(old.order_match_id)||',tx0_address='||quote(old.tx0_address)||',tx1_address='||quote(old.tx1_address)||',block_index='||quote(old.block_index)||' WHERE rowid='||old.rowid);
                            END;

-- Table  order_matches
DROP TABLE IF EXISTS order_matches;
CREATE TABLE order_matches(
                      id TEXT PRIMARY KEY,
                      tx0_index INTEGER,
                      tx0_hash TEXT,
                      tx0_address TEXT,
                      tx1_index INTEGER,
                      tx1_hash TEXT,
                      tx1_address TEXT,
                      forward_asset TEXT,
                      forward_quantity INTEGER,
                      backward_asset TEXT,
                      backward_quantity INTEGER,
                      tx0_block_index INTEGER,
                      tx1_block_index INTEGER,
                      block_index INTEGER,
                      tx0_expiration INTEGER,
                      tx1_expiration INTEGER,
                      match_expire_index INTEGER,
                      fee_paid INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx0_index, tx0_hash, tx0_block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                      FOREIGN KEY (tx1_index, tx1_hash, tx1_block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
INSERT INTO order_matches VALUES('6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59_36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c',3,'6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',4,'36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BTC',50000000,'XCP',100000000,310002,310003,310003,10,10,310023,857142,'completed');
-- Triggers and indices on  order_matches
CREATE TRIGGER _order_matches_delete BEFORE DELETE ON order_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO order_matches(rowid,id,tx0_index,tx0_hash,tx0_address,tx1_index,tx1_hash,tx1_address,forward_asset,forward_quantity,backward_asset,backward_quantity,tx0_block_index,tx1_block_index,block_index,tx0_expiration,tx1_expiration,match_expire_index,fee_paid,status) VALUES('||old.rowid||','||quote(old.id)||','||quote(old.tx0_index)||','||quote(old.tx0_hash)||','||quote(old.tx0_address)||','||quote(old.tx1_index)||','||quote(old.tx1_hash)||','||quote(old.tx1_address)||','||quote(old.forward_asset)||','||quote(old.forward_quantity)||','||quote(old.backward_asset)||','||quote(old.backward_quantity)||','||quote(old.tx0_block_index)||','||quote(old.tx1_block_index)||','||quote(old.block_index)||','||quote(old.tx0_expiration)||','||quote(old.tx1_expiration)||','||quote(old.match_expire_index)||','||quote(old.fee_paid)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _order_matches_insert AFTER INSERT ON order_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM order_matches WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _order_matches_update AFTER UPDATE ON order_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE order_matches SET id='||quote(old.id)||',tx0_index='||quote(old.tx0_index)||',tx0_hash='||quote(old.tx0_hash)||',tx0_address='||quote(old.tx0_address)||',tx1_index='||quote(old.tx1_index)||',tx1_hash='||quote(old.tx1_hash)||',tx1_address='||quote(old.tx1_address)||',forward_asset='||quote(old.forward_asset)||',forward_quantity='||quote(old.forward_quantity)||',backward_asset='||quote(old.backward_asset)||',backward_quantity='||quote(old.backward_quantity)||',tx0_block_index='||quote(old.tx0_block_index)||',tx1_block_index='||quote(old.tx1_block_index)||',block_index='||quote(old.block_index)||',tx0_expiration='||quote(old.tx0_expiration)||',tx1_expiration='||quote(old.tx1_expiration)||',match_expire_index='||quote(old.match_expire_index)||',fee_paid='||quote(old.fee_paid)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX backward_status_idx ON order_matches (backward_asset, status);
CREATE INDEX forward_status_idx ON order_matches (forward_asset, status);
CREATE INDEX match_expire_idx ON order_matches (status, match_expire_index);
CREATE INDEX tx0_address_idx ON order_matches (tx0_address);
CREATE INDEX tx1_address_idx ON order_matches (tx1_address);

-- Table  orders
DROP TABLE IF EXISTS orders;
CREATE TABLE orders(
                      tx_index INTEGER UNIQUE,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      give_asset TEXT,
                      give_quantity INTEGER,
                      give_remaining INTEGER,
                      get_asset TEXT,
                      get_quantity INTEGER,
                      get_remaining INTEGER,
                      expiration INTEGER,
                      expire_index INTEGER,
                      fee_required INTEGER,
                      fee_required_remaining INTEGER,
                      fee_provided INTEGER,
                      fee_provided_remaining INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                      PRIMARY KEY (tx_index, tx_hash));
INSERT INTO orders VALUES(3,'6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59',310002,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BTC',50000000,0,'XCP',100000000,0,10,310012,0,0,1000000,142858,'expired');
INSERT INTO orders VALUES(4,'36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c',310003,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','XCP',105000000,5000000,'BTC',50000000,0,10,310013,900000,42858,6800,6800,'expired');
INSERT INTO orders VALUES(22,'eb5953f4e1dec30f0bf4741cb2044c11b6e1c3be20fef2111461f69d989b852a',310021,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','BBBB',50000000,50000000,'XCP',50000000,50000000,10,310031,0,0,6800,6800,'expired');
-- Triggers and indices on  orders
CREATE TRIGGER _orders_delete BEFORE DELETE ON orders BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO orders(rowid,tx_index,tx_hash,block_index,source,give_asset,give_quantity,give_remaining,get_asset,get_quantity,get_remaining,expiration,expire_index,fee_required,fee_required_remaining,fee_provided,fee_provided_remaining,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.give_asset)||','||quote(old.give_quantity)||','||quote(old.give_remaining)||','||quote(old.get_asset)||','||quote(old.get_quantity)||','||quote(old.get_remaining)||','||quote(old.expiration)||','||quote(old.expire_index)||','||quote(old.fee_required)||','||quote(old.fee_required_remaining)||','||quote(old.fee_provided)||','||quote(old.fee_provided_remaining)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _orders_insert AFTER INSERT ON orders BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM orders WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _orders_update AFTER UPDATE ON orders BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE orders SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',give_asset='||quote(old.give_asset)||',give_quantity='||quote(old.give_quantity)||',give_remaining='||quote(old.give_remaining)||',get_asset='||quote(old.get_asset)||',get_quantity='||quote(old.get_quantity)||',get_remaining='||quote(old.get_remaining)||',expiration='||quote(old.expiration)||',expire_index='||quote(old.expire_index)||',fee_required='||quote(old.fee_required)||',fee_required_remaining='||quote(old.fee_required_remaining)||',fee_provided='||quote(old.fee_provided)||',fee_provided_remaining='||quote(old.fee_provided_remaining)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX expire_idx ON orders (expire_index, status);
CREATE INDEX give_asset_idx ON orders (give_asset);
CREATE INDEX give_get_status_idx ON orders (get_asset, give_asset, status);
CREATE INDEX give_status_idx ON orders (give_asset, status);
CREATE INDEX source_give_status_idx ON orders (source, give_asset, status);

-- Table  rps
DROP TABLE IF EXISTS rps;
CREATE TABLE rps(
                      tx_index INTEGER UNIQUE,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      possible_moves INTEGER,
                      wager INTEGER,
                      move_random_hash TEXT,
                      expiration INTEGER,
                      expire_index INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                      PRIMARY KEY (tx_index, tx_hash));
-- Triggers and indices on  rps
CREATE TRIGGER _rps_delete BEFORE DELETE ON rps BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO rps(rowid,tx_index,tx_hash,block_index,source,possible_moves,wager,move_random_hash,expiration,expire_index,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.possible_moves)||','||quote(old.wager)||','||quote(old.move_random_hash)||','||quote(old.expiration)||','||quote(old.expire_index)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _rps_insert AFTER INSERT ON rps BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM rps WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _rps_update AFTER UPDATE ON rps BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE rps SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',possible_moves='||quote(old.possible_moves)||',wager='||quote(old.wager)||',move_random_hash='||quote(old.move_random_hash)||',expiration='||quote(old.expiration)||',expire_index='||quote(old.expire_index)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX matching_idx ON rps (wager, possible_moves);

-- Table  rps_expirations
DROP TABLE IF EXISTS rps_expirations;
CREATE TABLE rps_expirations(
                      rps_index INTEGER PRIMARY KEY,
                      rps_hash TEXT UNIQUE,
                      source TEXT,
                      block_index INTEGER,
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index),
                      FOREIGN KEY (rps_index, rps_hash) REFERENCES rps(tx_index, tx_hash));
-- Triggers and indices on  rps_expirations
CREATE TRIGGER _rps_expirations_delete BEFORE DELETE ON rps_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO rps_expirations(rowid,rps_index,rps_hash,source,block_index) VALUES('||old.rowid||','||quote(old.rps_index)||','||quote(old.rps_hash)||','||quote(old.source)||','||quote(old.block_index)||')');
                            END;
CREATE TRIGGER _rps_expirations_insert AFTER INSERT ON rps_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM rps_expirations WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _rps_expirations_update AFTER UPDATE ON rps_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE rps_expirations SET rps_index='||quote(old.rps_index)||',rps_hash='||quote(old.rps_hash)||',source='||quote(old.source)||',block_index='||quote(old.block_index)||' WHERE rowid='||old.rowid);
                            END;

-- Table  rps_match_expirations
DROP TABLE IF EXISTS rps_match_expirations;
CREATE TABLE rps_match_expirations(
                      rps_match_id TEXT PRIMARY KEY,
                      tx0_address TEXT,
                      tx1_address TEXT,
                      block_index INTEGER,
                      FOREIGN KEY (rps_match_id) REFERENCES rps_matches(id),
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index));
-- Triggers and indices on  rps_match_expirations
CREATE TRIGGER _rps_match_expirations_delete BEFORE DELETE ON rps_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO rps_match_expirations(rowid,rps_match_id,tx0_address,tx1_address,block_index) VALUES('||old.rowid||','||quote(old.rps_match_id)||','||quote(old.tx0_address)||','||quote(old.tx1_address)||','||quote(old.block_index)||')');
                            END;
CREATE TRIGGER _rps_match_expirations_insert AFTER INSERT ON rps_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM rps_match_expirations WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _rps_match_expirations_update AFTER UPDATE ON rps_match_expirations BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE rps_match_expirations SET rps_match_id='||quote(old.rps_match_id)||',tx0_address='||quote(old.tx0_address)||',tx1_address='||quote(old.tx1_address)||',block_index='||quote(old.block_index)||' WHERE rowid='||old.rowid);
                            END;

-- Table  rps_matches
DROP TABLE IF EXISTS rps_matches;
CREATE TABLE rps_matches(
                      id TEXT PRIMARY KEY,
                      tx0_index INTEGER,
                      tx0_hash TEXT,
                      tx0_address TEXT,
                      tx1_index INTEGER,
                      tx1_hash TEXT,
                      tx1_address TEXT,
                      tx0_move_random_hash TEXT,
                      tx1_move_random_hash TEXT,
                      wager INTEGER,
                      possible_moves INTEGER,
                      tx0_block_index INTEGER,
                      tx1_block_index INTEGER,
                      block_index INTEGER,
                      tx0_expiration INTEGER,
                      tx1_expiration INTEGER,
                      match_expire_index INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx0_index, tx0_hash, tx0_block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                      FOREIGN KEY (tx1_index, tx1_hash, tx1_block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
-- Triggers and indices on  rps_matches
CREATE TRIGGER _rps_matches_delete BEFORE DELETE ON rps_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO rps_matches(rowid,id,tx0_index,tx0_hash,tx0_address,tx1_index,tx1_hash,tx1_address,tx0_move_random_hash,tx1_move_random_hash,wager,possible_moves,tx0_block_index,tx1_block_index,block_index,tx0_expiration,tx1_expiration,match_expire_index,status) VALUES('||old.rowid||','||quote(old.id)||','||quote(old.tx0_index)||','||quote(old.tx0_hash)||','||quote(old.tx0_address)||','||quote(old.tx1_index)||','||quote(old.tx1_hash)||','||quote(old.tx1_address)||','||quote(old.tx0_move_random_hash)||','||quote(old.tx1_move_random_hash)||','||quote(old.wager)||','||quote(old.possible_moves)||','||quote(old.tx0_block_index)||','||quote(old.tx1_block_index)||','||quote(old.block_index)||','||quote(old.tx0_expiration)||','||quote(old.tx1_expiration)||','||quote(old.match_expire_index)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _rps_matches_insert AFTER INSERT ON rps_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM rps_matches WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _rps_matches_update AFTER UPDATE ON rps_matches BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE rps_matches SET id='||quote(old.id)||',tx0_index='||quote(old.tx0_index)||',tx0_hash='||quote(old.tx0_hash)||',tx0_address='||quote(old.tx0_address)||',tx1_index='||quote(old.tx1_index)||',tx1_hash='||quote(old.tx1_hash)||',tx1_address='||quote(old.tx1_address)||',tx0_move_random_hash='||quote(old.tx0_move_random_hash)||',tx1_move_random_hash='||quote(old.tx1_move_random_hash)||',wager='||quote(old.wager)||',possible_moves='||quote(old.possible_moves)||',tx0_block_index='||quote(old.tx0_block_index)||',tx1_block_index='||quote(old.tx1_block_index)||',block_index='||quote(old.block_index)||',tx0_expiration='||quote(old.tx0_expiration)||',tx1_expiration='||quote(old.tx1_expiration)||',match_expire_index='||quote(old.match_expire_index)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX rps_match_expire_idx ON rps_matches (status, match_expire_index);
CREATE INDEX rps_tx0_address_idx ON rps_matches (tx0_address);
CREATE INDEX rps_tx1_address_idx ON rps_matches (tx1_address);

-- Table  rpsresolves
DROP TABLE IF EXISTS rpsresolves;
CREATE TABLE rpsresolves(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      move INTEGER,
                      random TEXT,
                      rps_match_id TEXT,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
-- Triggers and indices on  rpsresolves
CREATE TRIGGER _rpsresolves_delete BEFORE DELETE ON rpsresolves BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO rpsresolves(rowid,tx_index,tx_hash,block_index,source,move,random,rps_match_id,status) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.move)||','||quote(old.random)||','||quote(old.rps_match_id)||','||quote(old.status)||')');
                            END;
CREATE TRIGGER _rpsresolves_insert AFTER INSERT ON rpsresolves BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM rpsresolves WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _rpsresolves_update AFTER UPDATE ON rpsresolves BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE rpsresolves SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',move='||quote(old.move)||',random='||quote(old.random)||',rps_match_id='||quote(old.rps_match_id)||',status='||quote(old.status)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX rps_match_id_idx ON rpsresolves (rps_match_id);

-- Table  sends
DROP TABLE IF EXISTS sends;
CREATE TABLE "sends"(
                              tx_index INTEGER,
                              tx_hash TEXT,
                              block_index INTEGER,
                              source TEXT,
                              destination TEXT,
                              asset TEXT,
                              quantity INTEGER,
                              status TEXT,
                              msg_index INTEGER DEFAULT 0, memo BLOB,
                              PRIMARY KEY (tx_index, msg_index),
                              FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                              UNIQUE (tx_hash, msg_index) ON CONFLICT FAIL);
INSERT INTO sends VALUES(2,'3b273ba342ed8bd4ccd2ae28d3df7754768a6c65ec1cee4a6e84b4b4bdec8d8c',310001,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','XCP',50000000,'valid',0,NULL);
INSERT INTO sends VALUES(8,'5836fb23c2bb94eeb4b71cb8e3c622c6d943b3e4ed3aebee42d240445e615db8',310007,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','BBBB',4000000,'valid',0,NULL);
INSERT INTO sends VALUES(9,'843e6f7712b7847099502bda8a4bd7127c17a2799290b91ef1584a6bfe069412',310008,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','BBBC',526,'valid',0,NULL);
INSERT INTO sends VALUES(24,'58b89d056b539d2cf9ddac4518ccca6744495127e0ce893eb71da2599cbf85ab',310023,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns','BBBC',10000,'valid',0,NULL);
-- Triggers and indices on  sends
CREATE TRIGGER _sends_delete BEFORE DELETE ON sends BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO sends(rowid,tx_index,tx_hash,block_index,source,destination,asset,quantity,status,msg_index,memo) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.destination)||','||quote(old.asset)||','||quote(old.quantity)||','||quote(old.status)||','||quote(old.msg_index)||','||quote(old.memo)||')');
                            END;
CREATE TRIGGER _sends_insert AFTER INSERT ON sends BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM sends WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _sends_update AFTER UPDATE ON sends BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE sends SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',destination='||quote(old.destination)||',asset='||quote(old.asset)||',quantity='||quote(old.quantity)||',status='||quote(old.status)||',msg_index='||quote(old.msg_index)||',memo='||quote(old.memo)||' WHERE rowid='||old.rowid);
                            END;
CREATE INDEX destination_idx ON sends (destination);
CREATE INDEX memo_idx ON sends (memo);
CREATE INDEX source_idx ON sends (source);

-- Table  sweeps
DROP TABLE IF EXISTS sweeps;
CREATE TABLE sweeps(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      destination TEXT,
                      flags INTEGER,
                      status TEXT,
                      memo BLOB,
                      fee_paid INTEGER,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));
-- Triggers and indices on  sweeps
CREATE TRIGGER _sweeps_delete BEFORE DELETE ON sweeps BEGIN
                            INSERT INTO undolog VALUES(NULL, 'INSERT INTO sweeps(rowid,tx_index,tx_hash,block_index,source,destination,flags,status,memo,fee_paid) VALUES('||old.rowid||','||quote(old.tx_index)||','||quote(old.tx_hash)||','||quote(old.block_index)||','||quote(old.source)||','||quote(old.destination)||','||quote(old.flags)||','||quote(old.status)||','||quote(old.memo)||','||quote(old.fee_paid)||')');
                            END;
CREATE TRIGGER _sweeps_insert AFTER INSERT ON sweeps BEGIN
                            INSERT INTO undolog VALUES(NULL, 'DELETE FROM sweeps WHERE rowid='||new.rowid);
                            END;
CREATE TRIGGER _sweeps_update AFTER UPDATE ON sweeps BEGIN
                            INSERT INTO undolog VALUES(NULL, 'UPDATE sweeps SET tx_index='||quote(old.tx_index)||',tx_hash='||quote(old.tx_hash)||',block_index='||quote(old.block_index)||',source='||quote(old.source)||',destination='||quote(old.destination)||',flags='||quote(old.flags)||',status='||quote(old.status)||',memo='||quote(old.memo)||',fee_paid='||quote(old.fee_paid)||' WHERE rowid='||old.rowid);
                            END;

-- Table  transaction_outputs
DROP TABLE IF EXISTS transaction_outputs;
CREATE TABLE transaction_outputs(
                        tx_index,
                        tx_hash TEXT, 
                        block_index INTEGER,
                        out_index INTEGER,
                        destination TEXT,
                        btc_amount INTEGER,
                        PRIMARY KEY (tx_hash, out_index),
                        FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index));

-- Table  transactions
DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions(
                      tx_index INTEGER UNIQUE,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      block_hash TEXT,
                      block_time INTEGER,
                      source TEXT,
                      destination TEXT,
                      btc_amount INTEGER,
                      fee INTEGER,
                      data BLOB,
                      supported BOOL DEFAULT 1,
                      FOREIGN KEY (block_index, block_hash) REFERENCES blocks(block_index, block_hash),
                      PRIMARY KEY (tx_index, tx_hash, block_index));
INSERT INTO transactions VALUES(1,'6dc5b0a33d4d4297e0f5cc2d23ae307951d32aab2d86b7fa147b385219f3a597',310000,'505d8d82c4ced7daddef7ed0b05ba12ecc664176887b938ef56c6af276f3b30c',310000000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mvCounterpartyXXXXXXXXXXXXXXW24Hef',62000000,5625,X'',1);
INSERT INTO transactions VALUES(2,'3b273ba342ed8bd4ccd2ae28d3df7754768a6c65ec1cee4a6e84b4b4bdec8d8c',310001,'3c9f6a9c6cac46a9273bd3db39ad775acd5bc546378ec2fb0587e06e112cc78e',310001000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns',5430,7650,X'0000000000000000000000010000000002FAF080',1);
INSERT INTO transactions VALUES(3,'6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59',310002,'fbb60f1144e1f7d4dc036a4a158a10ea6dea2ba6283a723342a49b8eb5cc9964',310002000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,1000000,X'0000000A00000000000000000000000002FAF08000000000000000010000000005F5E100000A0000000000000000',1);
INSERT INTO transactions VALUES(4,'36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c',310003,'d50825dcb32bcf6f69994d616eba18de7718d3d859497e80751b2cb67e333e8a',310003000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'0000000A00000000000000010000000006422C4000000000000000000000000002FAF080000A00000000000DBBA0',1);
INSERT INTO transactions VALUES(5,'843c5df8f979db230ba61f26ad1342ed5803adeba7333b019b8a96ac6703f099',310004,'60cdc0ac0e3121ceaa2c3885f21f5789f49992ffef6e6ff99f7da80e36744615',310004000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',50000000,9675,X'0000000B6BDB2EF465E9FC04060F58CED26C159DC983A616CB121C5E7954E66833444C5936D00F8C35A9C6ECC7DD0A64610B1C39A71110D1A95FACE6A2486A6A7A1FF83C',1);
INSERT INTO transactions VALUES(6,'5d951d44d034cb6fd5dc5c98cd877c63f55c1ae108d335b6b6d991d072856adf',310005,'8005c2926b7ecc50376642bc661a49108b6dc62636463a5c492b123e2184cd9a',310005000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'000000140000000000004767000000003B9ACA000100000000000000000000',1);
INSERT INTO transactions VALUES(7,'41c590d8bc8a0bd0e436c4c50e14c2ce86df3cd3450336bff5d01cdf7f122753',310006,'bdad69d1669eace68b9f246de113161099d4f83322e2acf402c42defef3af2bb',310006000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'00000014000000000000476800000000000186A00000000000000000000000',1);
INSERT INTO transactions VALUES(8,'5836fb23c2bb94eeb4b71cb8e3c622c6d943b3e4ed3aebee42d240445e615db8',310007,'10a642b96d60091d08234d17dfdecf3025eca41e4fc8e3bbe71a91c5a457cb4b',310007000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns',5430,7650,X'00000000000000000000476700000000003D0900',1);
INSERT INTO transactions VALUES(9,'843e6f7712b7847099502bda8a4bd7127c17a2799290b91ef1584a6bfe069412',310008,'47d0e3acbdc6916aeae95e987f9cfa16209b3df1e67bb38143b3422b32322c33',310008000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns',5430,7650,X'000000000000000000004768000000000000020E',1);
INSERT INTO transactions VALUES(10,'42ae2fd7f3a18f84334bc37aa88283e79d6bff0b234dbf97e788695957d75518',310009,'4d474992b141620bf3753863db7ee5e8af26cadfbba27725911f44fa657bc1c0',310009000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'00000032000000000000025800000000000047670000000000000001',1);
INSERT INTO transactions VALUES(11,'201123e1ddbc4dab954fed0043a29fca770a9bd4268714354bb7991f01133c10',310010,'a58162dff81a32e6a29b075be759dbb9fa9b8b65303e69c78fb4d7b0acc37042',310010000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'00000032000000000000032000000000000047680000000000000001',1);
INSERT INTO transactions VALUES(12,'1afa4fa28e1ef63b2b67c288e078cfeb109a2b236558ab5544eedc7f171e0a84',310011,'8042cc2ef293fd73d050f283fbd075c79dd4c49fdcca054dc0714fc3a50dc1bb',310011000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'0000001E52BB3300405900000000000005F5E0FF09556E69742054657374',1);
INSERT INTO transactions VALUES(13,'7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81',310012,'cdba329019d93a67b31b79d05f76ce1b7791d430ea0d6c1c2168fe78d2f67677',310012000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',5430,7650,X'00000028000052BB33640000000002FAF08000000000017D7840000000000000000000003B100000000A',1);
INSERT INTO transactions VALUES(14,'e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42',310013,'0425e5e832e4286757dc0228cd505b8d572081007218abd3a0983a3bcd502a61',310013000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',5430,7650,X'00000028000152BB336400000000017D78400000000002793D60000000000000000000003B100000000A',1);
INSERT INTO transactions VALUES(15,'3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a',310014,'85b28d413ebda2968ed82ae53643677338650151b997ed1e4656158005b9f65f',310014000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',5430,7650,X'00000028000052BB33640000000008F0D1800000000014DC93800000000000000000000013B00000000A',1);
INSERT INTO transactions VALUES(16,'a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8',310015,'4cf77d688f18f0c68c077db882f62e49f31859dfa6144372457cd73b29223922',310015000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',5430,7650,X'00000028000152BB33640000000014DC93800000000008F0D1800000000000000000000013B00000000A',1);
INSERT INTO transactions VALUES(17,'194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5',310016,'99dc7d2627efb4e5e618a53b9898b4ca39c70e98fe9bf39f68a6c980f5b64ef9',310016000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',5430,7650,X'00000028000252BB33C8000000002CB417800000000026BE36803FF0000000000000000013B00000000A',1);
INSERT INTO transactions VALUES(18,'72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207',310017,'8a4fedfbf734b91a5c5761a7bcb3908ea57169777a7018148c51ff611970e4a3',310017000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',5430,7650,X'00000028000352BB33C80000000026BE3680000000002CB417803FF0000000000000000013B00000000A',1);
INSERT INTO transactions VALUES(19,'065de641fd87c0b3ef893130ef4a3dca7643b7a35f6d18c721f34a7a36a5992f',310018,'35c06f9e3de39e4e56ceb1d1a22008f52361c50dd0d251c0acbe2e3c2dba8ed3',310018000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'0000001E52BB33324058F7256FFC115E004C4B4009556E69742054657374',1);
INSERT INTO transactions VALUES(20,'7cc015005c559686a8e10294015ca1773c0bcd9f4d7d9768deb4bb94cdd4a69e',310019,'114affa0c4f34b1ebf8e2778c9477641f60b5b9e8a69052158041d4c41893294',310019000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'0000001E52BB3365405915F3B645A1CB004C4B4009556E69742054657374',1);
INSERT INTO transactions VALUES(21,'0899b8bccef3403252fd7d37ec550eea3350845dca098368b84bf4c3c48d3fc9',310020,'d93c79920e4a42164af74ecb5c6b903ff6055cdc007376c74dfa692c8d85ebc9',310020000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'0000001E52BB33C94000000000000000004C4B4009556E69742054657374',1);
INSERT INTO transactions VALUES(22,'eb5953f4e1dec30f0bf4741cb2044c11b6e1c3be20fef2111461f69d989b852a',310021,'7c2460bb32c5749c856486393239bf7a0ac789587ac71f32e7237910da8097f2',310021000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','',0,6800,X'0000000A00000000000047670000000002FAF08000000000000000010000000002FAF080000A0000000000000000',1);
INSERT INTO transactions VALUES(23,'c3f73d02e630cb2824f044e6d91f47b1ce351feff0339ea7b85652d24d8ff6bc',310022,'44435f9a99a0aa12a9bfabdc4cb8119f6ea6a6e1350d2d65445fb66a456db5fc',310022000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mvCounterpartyXXXXXXXXXXXXXXW24Hef',100000000,10150,X'',1);
INSERT INTO transactions VALUES(24,'58b89d056b539d2cf9ddac4518ccca6744495127e0ce893eb71da2599cbf85ab',310023,'d8cf5bec1bbcab8ca4f495352afde3b6572b7e1d61b3976872ebb8e9d30ccb08',310023000,'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc','mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns',5430,7650,X'0000000000000000000047680000000000002710',1);
-- Triggers and indices on  transactions
CREATE INDEX index_hash_index_idx ON transactions (tx_index, tx_hash, block_index);
CREATE INDEX index_index_idx ON transactions (block_index, tx_index);
CREATE INDEX tx_hash_idx ON transactions (tx_hash);
CREATE INDEX tx_index_idx ON transactions (tx_index);

-- Table  undolog
DROP TABLE IF EXISTS undolog;
CREATE TABLE undolog(
                        undo_index INTEGER PRIMARY KEY AUTOINCREMENT,
                        sql TEXT);
INSERT INTO undolog VALUES(4,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=93000000000 WHERE rowid=1');
INSERT INTO undolog VALUES(5,'DELETE FROM debits WHERE rowid=1');
INSERT INTO undolog VALUES(6,'DELETE FROM balances WHERE rowid=2');
INSERT INTO undolog VALUES(7,'DELETE FROM credits WHERE rowid=2');
INSERT INTO undolog VALUES(8,'DELETE FROM sends WHERE rowid=1');
INSERT INTO undolog VALUES(9,'DELETE FROM orders WHERE rowid=1');
INSERT INTO undolog VALUES(10,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92950000000 WHERE rowid=1');
INSERT INTO undolog VALUES(11,'DELETE FROM debits WHERE rowid=2');
INSERT INTO undolog VALUES(12,'DELETE FROM orders WHERE rowid=2');
INSERT INTO undolog VALUES(13,'UPDATE orders SET tx_index=3,tx_hash=''6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59'',block_index=310002,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',give_asset=''BTC'',give_quantity=50000000,give_remaining=50000000,get_asset=''XCP'',get_quantity=100000000,get_remaining=100000000,expiration=10,expire_index=310012,fee_required=0,fee_required_remaining=0,fee_provided=1000000,fee_provided_remaining=1000000,status=''open'' WHERE rowid=1');
INSERT INTO undolog VALUES(14,'UPDATE orders SET tx_index=4,tx_hash=''36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c'',block_index=310003,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',give_asset=''XCP'',give_quantity=105000000,give_remaining=105000000,get_asset=''BTC'',get_quantity=50000000,get_remaining=50000000,expiration=10,expire_index=310013,fee_required=900000,fee_required_remaining=900000,fee_provided=6800,fee_provided_remaining=6800,status=''open'' WHERE rowid=2');
INSERT INTO undolog VALUES(15,'DELETE FROM order_matches WHERE rowid=1');
INSERT INTO undolog VALUES(16,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92845000000 WHERE rowid=1');
INSERT INTO undolog VALUES(17,'DELETE FROM credits WHERE rowid=3');
INSERT INTO undolog VALUES(18,'UPDATE order_matches SET id=''6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59_36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c'',tx0_index=3,tx0_hash=''6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59'',tx0_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',tx1_index=4,tx1_hash=''36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c'',tx1_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',forward_asset=''BTC'',forward_quantity=50000000,backward_asset=''XCP'',backward_quantity=100000000,tx0_block_index=310002,tx1_block_index=310003,block_index=310003,tx0_expiration=10,tx1_expiration=10,match_expire_index=310023,fee_paid=857142,status=''pending'' WHERE rowid=1');
INSERT INTO undolog VALUES(19,'DELETE FROM btcpays WHERE rowid=5');
INSERT INTO undolog VALUES(20,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92945000000 WHERE rowid=1');
INSERT INTO undolog VALUES(21,'DELETE FROM debits WHERE rowid=3');
INSERT INTO undolog VALUES(22,'DELETE FROM assets WHERE rowid=3');
INSERT INTO undolog VALUES(23,'DELETE FROM issuances WHERE rowid=1');
INSERT INTO undolog VALUES(24,'DELETE FROM balances WHERE rowid=3');
INSERT INTO undolog VALUES(25,'DELETE FROM credits WHERE rowid=4');
INSERT INTO undolog VALUES(26,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92895000000 WHERE rowid=1');
INSERT INTO undolog VALUES(27,'DELETE FROM debits WHERE rowid=4');
INSERT INTO undolog VALUES(28,'DELETE FROM assets WHERE rowid=4');
INSERT INTO undolog VALUES(29,'DELETE FROM issuances WHERE rowid=2');
INSERT INTO undolog VALUES(30,'DELETE FROM balances WHERE rowid=4');
INSERT INTO undolog VALUES(31,'DELETE FROM credits WHERE rowid=5');
INSERT INTO undolog VALUES(32,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''BBBB'',quantity=1000000000 WHERE rowid=3');
INSERT INTO undolog VALUES(33,'DELETE FROM debits WHERE rowid=5');
INSERT INTO undolog VALUES(34,'DELETE FROM balances WHERE rowid=5');
INSERT INTO undolog VALUES(35,'DELETE FROM credits WHERE rowid=6');
INSERT INTO undolog VALUES(36,'DELETE FROM sends WHERE rowid=2');
INSERT INTO undolog VALUES(37,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''BBBC'',quantity=100000 WHERE rowid=4');
INSERT INTO undolog VALUES(38,'DELETE FROM debits WHERE rowid=6');
INSERT INTO undolog VALUES(39,'DELETE FROM balances WHERE rowid=6');
INSERT INTO undolog VALUES(40,'DELETE FROM credits WHERE rowid=7');
INSERT INTO undolog VALUES(41,'DELETE FROM sends WHERE rowid=3');
INSERT INTO undolog VALUES(42,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92845000000 WHERE rowid=1');
INSERT INTO undolog VALUES(43,'DELETE FROM debits WHERE rowid=7');
INSERT INTO undolog VALUES(44,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92844999976 WHERE rowid=1');
INSERT INTO undolog VALUES(45,'DELETE FROM debits WHERE rowid=8');
INSERT INTO undolog VALUES(46,'UPDATE balances SET address=''mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns'',asset=''XCP'',quantity=50000000 WHERE rowid=2');
INSERT INTO undolog VALUES(47,'DELETE FROM credits WHERE rowid=8');
INSERT INTO undolog VALUES(48,'DELETE FROM dividends WHERE rowid=10');
INSERT INTO undolog VALUES(49,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92844979976 WHERE rowid=1');
INSERT INTO undolog VALUES(50,'DELETE FROM debits WHERE rowid=9');
INSERT INTO undolog VALUES(51,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92844559176 WHERE rowid=1');
INSERT INTO undolog VALUES(52,'DELETE FROM debits WHERE rowid=10');
INSERT INTO undolog VALUES(53,'UPDATE balances SET address=''mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns'',asset=''XCP'',quantity=50000024 WHERE rowid=2');
INSERT INTO undolog VALUES(54,'DELETE FROM credits WHERE rowid=9');
INSERT INTO undolog VALUES(55,'DELETE FROM dividends WHERE rowid=11');
INSERT INTO undolog VALUES(56,'DELETE FROM broadcasts WHERE rowid=12');
INSERT INTO undolog VALUES(57,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92844539176 WHERE rowid=1');
INSERT INTO undolog VALUES(58,'DELETE FROM debits WHERE rowid=11');
INSERT INTO undolog VALUES(59,'DELETE FROM bets WHERE rowid=1');
INSERT INTO undolog VALUES(60,'UPDATE orders SET tx_index=3,tx_hash=''6bdb2ef465e9fc04060f58ced26c159dc983a616cb121c5e7954e66833444c59'',block_index=310002,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',give_asset=''BTC'',give_quantity=50000000,give_remaining=0,get_asset=''XCP'',get_quantity=100000000,get_remaining=0,expiration=10,expire_index=310012,fee_required=0,fee_required_remaining=0,fee_provided=1000000,fee_provided_remaining=142858,status=''open'' WHERE rowid=1');
INSERT INTO undolog VALUES(61,'DELETE FROM order_expirations WHERE rowid=3');
INSERT INTO undolog VALUES(62,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92794539176 WHERE rowid=1');
INSERT INTO undolog VALUES(63,'DELETE FROM debits WHERE rowid=12');
INSERT INTO undolog VALUES(64,'DELETE FROM bets WHERE rowid=2');
INSERT INTO undolog VALUES(65,'UPDATE bets SET tx_index=13,tx_hash=''7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81'',block_index=310012,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',bet_type=0,deadline=1388000100,wager_quantity=50000000,wager_remaining=50000000,counterwager_quantity=25000000,counterwager_remaining=25000000,target_value=0.0,leverage=15120,expiration=10,expire_index=310022,fee_fraction_int=99999999,status=''open'' WHERE rowid=1');
INSERT INTO undolog VALUES(66,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92769539176 WHERE rowid=1');
INSERT INTO undolog VALUES(67,'DELETE FROM credits WHERE rowid=10');
INSERT INTO undolog VALUES(68,'UPDATE bets SET tx_index=14,tx_hash=''e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42'',block_index=310013,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',bet_type=1,deadline=1388000100,wager_quantity=25000000,wager_remaining=25000000,counterwager_quantity=41500000,counterwager_remaining=41500000,target_value=0.0,leverage=15120,expiration=10,expire_index=310023,fee_fraction_int=99999999,status=''open'' WHERE rowid=2');
INSERT INTO undolog VALUES(69,'DELETE FROM bet_matches WHERE rowid=1');
INSERT INTO undolog VALUES(70,'UPDATE orders SET tx_index=4,tx_hash=''36d00f8c35a9c6ecc7dd0a64610b1c39a71110d1a95face6a2486a6a7a1ff83c'',block_index=310003,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',give_asset=''XCP'',give_quantity=105000000,give_remaining=5000000,get_asset=''BTC'',get_quantity=50000000,get_remaining=0,expiration=10,expire_index=310013,fee_required=900000,fee_required_remaining=42858,fee_provided=6800,fee_provided_remaining=6800,status=''open'' WHERE rowid=2');
INSERT INTO undolog VALUES(71,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92773789176 WHERE rowid=1');
INSERT INTO undolog VALUES(72,'DELETE FROM credits WHERE rowid=11');
INSERT INTO undolog VALUES(73,'DELETE FROM order_expirations WHERE rowid=4');
INSERT INTO undolog VALUES(74,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92778789176 WHERE rowid=1');
INSERT INTO undolog VALUES(75,'DELETE FROM debits WHERE rowid=13');
INSERT INTO undolog VALUES(76,'DELETE FROM bets WHERE rowid=3');
INSERT INTO undolog VALUES(77,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92628789176 WHERE rowid=1');
INSERT INTO undolog VALUES(78,'DELETE FROM debits WHERE rowid=14');
INSERT INTO undolog VALUES(79,'DELETE FROM bets WHERE rowid=4');
INSERT INTO undolog VALUES(80,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92278789176 WHERE rowid=1');
INSERT INTO undolog VALUES(81,'DELETE FROM credits WHERE rowid=12');
INSERT INTO undolog VALUES(82,'UPDATE bets SET tx_index=15,tx_hash=''3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a'',block_index=310014,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',bet_type=0,deadline=1388000100,wager_quantity=150000000,wager_remaining=150000000,counterwager_quantity=350000000,counterwager_remaining=350000000,target_value=0.0,leverage=5040,expiration=10,expire_index=310024,fee_fraction_int=99999999,status=''open'' WHERE rowid=3');
INSERT INTO undolog VALUES(83,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92278789176 WHERE rowid=1');
INSERT INTO undolog VALUES(84,'DELETE FROM credits WHERE rowid=13');
INSERT INTO undolog VALUES(85,'UPDATE bets SET tx_index=16,tx_hash=''a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8'',block_index=310015,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',bet_type=1,deadline=1388000100,wager_quantity=350000000,wager_remaining=350000000,counterwager_quantity=150000000,counterwager_remaining=150000000,target_value=0.0,leverage=5040,expiration=10,expire_index=310025,fee_fraction_int=99999999,status=''open'' WHERE rowid=4');
INSERT INTO undolog VALUES(86,'DELETE FROM bet_matches WHERE rowid=2');
INSERT INTO undolog VALUES(87,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92278789176 WHERE rowid=1');
INSERT INTO undolog VALUES(88,'DELETE FROM debits WHERE rowid=15');
INSERT INTO undolog VALUES(89,'DELETE FROM bets WHERE rowid=5');
INSERT INTO undolog VALUES(90,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=91528789176 WHERE rowid=1');
INSERT INTO undolog VALUES(91,'DELETE FROM debits WHERE rowid=16');
INSERT INTO undolog VALUES(92,'DELETE FROM bets WHERE rowid=6');
INSERT INTO undolog VALUES(93,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=90878789176 WHERE rowid=1');
INSERT INTO undolog VALUES(94,'DELETE FROM credits WHERE rowid=14');
INSERT INTO undolog VALUES(95,'UPDATE bets SET tx_index=17,tx_hash=''194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5'',block_index=310016,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',bet_type=2,deadline=1388000200,wager_quantity=750000000,wager_remaining=750000000,counterwager_quantity=650000000,counterwager_remaining=650000000,target_value=1.0,leverage=5040,expiration=10,expire_index=310026,fee_fraction_int=99999999,status=''open'' WHERE rowid=5');
INSERT INTO undolog VALUES(96,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=90878789176 WHERE rowid=1');
INSERT INTO undolog VALUES(97,'DELETE FROM credits WHERE rowid=15');
INSERT INTO undolog VALUES(98,'UPDATE bets SET tx_index=18,tx_hash=''72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207'',block_index=310017,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',bet_type=3,deadline=1388000200,wager_quantity=650000000,wager_remaining=650000000,counterwager_quantity=750000000,counterwager_remaining=750000000,target_value=1.0,leverage=5040,expiration=10,expire_index=310027,fee_fraction_int=99999999,status=''open'' WHERE rowid=6');
INSERT INTO undolog VALUES(99,'DELETE FROM bet_matches WHERE rowid=3');
INSERT INTO undolog VALUES(100,'DELETE FROM broadcasts WHERE rowid=19');
INSERT INTO undolog VALUES(101,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=90878789176 WHERE rowid=1');
INSERT INTO undolog VALUES(102,'DELETE FROM credits WHERE rowid=16');
INSERT INTO undolog VALUES(103,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=90937926676 WHERE rowid=1');
INSERT INTO undolog VALUES(104,'DELETE FROM credits WHERE rowid=17');
INSERT INTO undolog VALUES(105,'DELETE FROM bet_match_resolutions WHERE rowid=1');
INSERT INTO undolog VALUES(106,'UPDATE bet_matches SET id=''7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81_e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42'',tx0_index=13,tx0_hash=''7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81'',tx0_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',tx1_index=14,tx1_hash=''e566ab052d414d2c9b9d6ffc643bc5d2b31d80976dffe7acceaf2576246f9e42'',tx1_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',tx0_bet_type=0,tx1_bet_type=1,feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',initial_value=100,deadline=1388000100,target_value=0.0,leverage=15120,forward_quantity=41500000,backward_quantity=20750000,tx0_block_index=310012,tx1_block_index=310013,block_index=310013,tx0_expiration=10,tx1_expiration=10,match_expire_index=310022,fee_fraction_int=99999999,status=''pending'' WHERE rowid=1');
INSERT INTO undolog VALUES(107,'DELETE FROM broadcasts WHERE rowid=20');
INSERT INTO undolog VALUES(108,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=90941039176 WHERE rowid=1');
INSERT INTO undolog VALUES(109,'DELETE FROM credits WHERE rowid=18');
INSERT INTO undolog VALUES(110,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=91100339176 WHERE rowid=1');
INSERT INTO undolog VALUES(111,'DELETE FROM credits WHERE rowid=19');
INSERT INTO undolog VALUES(112,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=91416039176 WHERE rowid=1');
INSERT INTO undolog VALUES(113,'DELETE FROM credits WHERE rowid=20');
INSERT INTO undolog VALUES(114,'DELETE FROM bet_match_resolutions WHERE rowid=2');
INSERT INTO undolog VALUES(115,'UPDATE bet_matches SET id=''3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a_a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8'',tx0_index=15,tx0_hash=''3d3ae119aa3891770b7ae1e1ce34062b7a850593f39a96b6df19d69960d4a76a'',tx0_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',tx1_index=16,tx1_hash=''a73843f1c9197674ba45e3aa92ed0671062c8acd8955e6b1e4d10dd149f40bc8'',tx1_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',tx0_bet_type=0,tx1_bet_type=1,feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',initial_value=100,deadline=1388000100,target_value=0.0,leverage=5040,forward_quantity=150000000,backward_quantity=350000000,tx0_block_index=310014,tx1_block_index=310015,block_index=310015,tx0_expiration=10,tx1_expiration=10,match_expire_index=310024,fee_fraction_int=99999999,status=''pending'' WHERE rowid=2');
INSERT INTO undolog VALUES(116,'DELETE FROM broadcasts WHERE rowid=21');
INSERT INTO undolog VALUES(117,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=91441039176 WHERE rowid=1');
INSERT INTO undolog VALUES(118,'DELETE FROM credits WHERE rowid=21');
INSERT INTO undolog VALUES(119,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92771039176 WHERE rowid=1');
INSERT INTO undolog VALUES(120,'DELETE FROM credits WHERE rowid=22');
INSERT INTO undolog VALUES(121,'DELETE FROM bet_match_resolutions WHERE rowid=3');
INSERT INTO undolog VALUES(122,'UPDATE bet_matches SET id=''194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5_72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207'',tx0_index=17,tx0_hash=''194a87d56aecedf43bb9724b6f20f10626c26c00267fd108db843772e5ee41f5'',tx0_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',tx1_index=18,tx1_hash=''72baa141e136cbafc08ee2f6c8e5841076c7573d5d5cd619f45149bf84a6a207'',tx1_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',tx0_bet_type=2,tx1_bet_type=3,feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',initial_value=100,deadline=1388000200,target_value=1.0,leverage=5040,forward_quantity=750000000,backward_quantity=650000000,tx0_block_index=310016,tx1_block_index=310017,block_index=310017,tx0_expiration=10,tx1_expiration=10,match_expire_index=310026,fee_fraction_int=99999999,status=''pending'' WHERE rowid=3');
INSERT INTO undolog VALUES(123,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''BBBB'',quantity=996000000 WHERE rowid=3');
INSERT INTO undolog VALUES(124,'DELETE FROM debits WHERE rowid=17');
INSERT INTO undolog VALUES(125,'DELETE FROM orders WHERE rowid=3');
INSERT INTO undolog VALUES(126,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=92841039176 WHERE rowid=1');
INSERT INTO undolog VALUES(127,'DELETE FROM credits WHERE rowid=23');
INSERT INTO undolog VALUES(128,'DELETE FROM burns WHERE rowid=23');
INSERT INTO undolog VALUES(129,'UPDATE bets SET tx_index=13,tx_hash=''7025ded3ba412d1285be69c8aaa02773b8f4e2504310832c99a9b171b7e07e81'',block_index=310012,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',feed_address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',bet_type=0,deadline=1388000100,wager_quantity=50000000,wager_remaining=8500000,counterwager_quantity=25000000,counterwager_remaining=4250000,target_value=0.0,leverage=15120,expiration=10,expire_index=310022,fee_fraction_int=99999999,status=''open'' WHERE rowid=1');
INSERT INTO undolog VALUES(130,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''XCP'',quantity=149840926438 WHERE rowid=1');
INSERT INTO undolog VALUES(131,'DELETE FROM credits WHERE rowid=24');
INSERT INTO undolog VALUES(132,'DELETE FROM bet_expirations WHERE rowid=13');
INSERT INTO undolog VALUES(133,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''BBBC'',quantity=99474 WHERE rowid=4');
INSERT INTO undolog VALUES(134,'DELETE FROM debits WHERE rowid=18');
INSERT INTO undolog VALUES(135,'UPDATE balances SET address=''mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns'',asset=''BBBC'',quantity=526 WHERE rowid=6');
INSERT INTO undolog VALUES(136,'DELETE FROM credits WHERE rowid=25');
INSERT INTO undolog VALUES(137,'DELETE FROM sends WHERE rowid=4');
INSERT INTO undolog VALUES(138,'UPDATE orders SET tx_index=22,tx_hash=''eb5953f4e1dec30f0bf4741cb2044c11b6e1c3be20fef2111461f69d989b852a'',block_index=310021,source=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',give_asset=''BBBB'',give_quantity=50000000,give_remaining=50000000,get_asset=''XCP'',get_quantity=50000000,get_remaining=50000000,expiration=10,expire_index=310031,fee_required=0,fee_required_remaining=0,fee_provided=6800,fee_provided_remaining=6800,status=''open'' WHERE rowid=3');
INSERT INTO undolog VALUES(139,'UPDATE balances SET address=''mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc'',asset=''BBBB'',quantity=946000000 WHERE rowid=3');
INSERT INTO undolog VALUES(140,'DELETE FROM credits WHERE rowid=26');
INSERT INTO undolog VALUES(141,'DELETE FROM order_expirations WHERE rowid=22');

-- Table  undolog_block
DROP TABLE IF EXISTS undolog_block;
CREATE TABLE undolog_block(
                        block_index INTEGER PRIMARY KEY,
                        first_undo_index INTEGER);
INSERT INTO undolog_block VALUES(310001,4);
INSERT INTO undolog_block VALUES(310002,9);
INSERT INTO undolog_block VALUES(310003,10);
INSERT INTO undolog_block VALUES(310004,16);
INSERT INTO undolog_block VALUES(310005,20);
INSERT INTO undolog_block VALUES(310006,26);
INSERT INTO undolog_block VALUES(310007,32);
INSERT INTO undolog_block VALUES(310008,37);
INSERT INTO undolog_block VALUES(310009,42);
INSERT INTO undolog_block VALUES(310010,49);
INSERT INTO undolog_block VALUES(310011,56);
INSERT INTO undolog_block VALUES(310012,57);
INSERT INTO undolog_block VALUES(310013,60);
INSERT INTO undolog_block VALUES(310014,70);
INSERT INTO undolog_block VALUES(310015,77);
INSERT INTO undolog_block VALUES(310016,87);
INSERT INTO undolog_block VALUES(310017,90);
INSERT INTO undolog_block VALUES(310018,100);
INSERT INTO undolog_block VALUES(310019,107);
INSERT INTO undolog_block VALUES(310020,116);
INSERT INTO undolog_block VALUES(310021,123);
INSERT INTO undolog_block VALUES(310022,126);
INSERT INTO undolog_block VALUES(310023,129);
INSERT INTO undolog_block VALUES(310024,138);
INSERT INTO undolog_block VALUES(310025,138);
INSERT INTO undolog_block VALUES(310026,138);
INSERT INTO undolog_block VALUES(310027,138);
INSERT INTO undolog_block VALUES(310028,138);
INSERT INTO undolog_block VALUES(310029,138);
INSERT INTO undolog_block VALUES(310030,138);
INSERT INTO undolog_block VALUES(310031,138);
INSERT INTO undolog_block VALUES(310032,138);
INSERT INTO undolog_block VALUES(310033,142);
INSERT INTO undolog_block VALUES(310034,142);
INSERT INTO undolog_block VALUES(310035,142);
INSERT INTO undolog_block VALUES(310036,142);
INSERT INTO undolog_block VALUES(310037,142);
INSERT INTO undolog_block VALUES(310038,142);
INSERT INTO undolog_block VALUES(310039,142);
INSERT INTO undolog_block VALUES(310040,142);
INSERT INTO undolog_block VALUES(310041,142);
INSERT INTO undolog_block VALUES(310042,142);
INSERT INTO undolog_block VALUES(310043,142);
INSERT INTO undolog_block VALUES(310044,142);
INSERT INTO undolog_block VALUES(310045,142);
INSERT INTO undolog_block VALUES(310046,142);
INSERT INTO undolog_block VALUES(310047,142);
INSERT INTO undolog_block VALUES(310048,142);
INSERT INTO undolog_block VALUES(310049,142);
INSERT INTO undolog_block VALUES(310050,142);
INSERT INTO undolog_block VALUES(310051,142);
INSERT INTO undolog_block VALUES(310052,142);
INSERT INTO undolog_block VALUES(310053,142);
INSERT INTO undolog_block VALUES(310054,142);
INSERT INTO undolog_block VALUES(310055,142);
INSERT INTO undolog_block VALUES(310056,142);
INSERT INTO undolog_block VALUES(310057,142);
INSERT INTO undolog_block VALUES(310058,142);
INSERT INTO undolog_block VALUES(310059,142);
INSERT INTO undolog_block VALUES(310060,142);
INSERT INTO undolog_block VALUES(310061,142);
INSERT INTO undolog_block VALUES(310062,142);
INSERT INTO undolog_block VALUES(310063,142);
INSERT INTO undolog_block VALUES(310064,142);
INSERT INTO undolog_block VALUES(310065,142);
INSERT INTO undolog_block VALUES(310066,142);
INSERT INTO undolog_block VALUES(310067,142);
INSERT INTO undolog_block VALUES(310068,142);
INSERT INTO undolog_block VALUES(310069,142);
INSERT INTO undolog_block VALUES(310070,142);
INSERT INTO undolog_block VALUES(310071,142);
INSERT INTO undolog_block VALUES(310072,142);
INSERT INTO undolog_block VALUES(310073,142);
INSERT INTO undolog_block VALUES(310074,142);
INSERT INTO undolog_block VALUES(310075,142);
INSERT INTO undolog_block VALUES(310076,142);
INSERT INTO undolog_block VALUES(310077,142);
INSERT INTO undolog_block VALUES(310078,142);
INSERT INTO undolog_block VALUES(310079,142);
INSERT INTO undolog_block VALUES(310080,142);
INSERT INTO undolog_block VALUES(310081,142);
INSERT INTO undolog_block VALUES(310082,142);
INSERT INTO undolog_block VALUES(310083,142);
INSERT INTO undolog_block VALUES(310084,142);
INSERT INTO undolog_block VALUES(310085,142);
INSERT INTO undolog_block VALUES(310086,142);
INSERT INTO undolog_block VALUES(310087,142);
INSERT INTO undolog_block VALUES(310088,142);
INSERT INTO undolog_block VALUES(310089,142);
INSERT INTO undolog_block VALUES(310090,142);
INSERT INTO undolog_block VALUES(310091,142);
INSERT INTO undolog_block VALUES(310092,142);
INSERT INTO undolog_block VALUES(310093,142);
INSERT INTO undolog_block VALUES(310094,142);
INSERT INTO undolog_block VALUES(310095,142);
INSERT INTO undolog_block VALUES(310096,142);
INSERT INTO undolog_block VALUES(310097,142);
INSERT INTO undolog_block VALUES(310098,142);
INSERT INTO undolog_block VALUES(310099,142);
INSERT INTO undolog_block VALUES(310100,142);
INSERT INTO undolog_block VALUES(310101,142);

-- For primary key autoincrements the next id to use is stored in
-- sqlite_sequence
DELETE FROM main.sqlite_sequence WHERE name='undolog';
INSERT INTO main.sqlite_sequence VALUES ('undolog', 141);

COMMIT TRANSACTION;
