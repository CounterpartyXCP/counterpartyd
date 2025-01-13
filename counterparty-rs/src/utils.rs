use bitcoin::blockdata::opcodes;
use bitcoin::blockdata::opcodes::all::*;
use bitcoin::blockdata::script::Instruction;
use bitcoin::{Address, Network, ScriptBuf, WitnessProgram, WitnessVersion};
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use pyo3::wrap_pyfunction;
use std::panic;

#[pyfunction]
fn inverse_hash(hashstring: &str) -> String {
    hashstring
        .chars()
        .rev()
        .collect::<Vec<char>>()
        .chunks(2)
        .flat_map(|chunk| chunk.iter().rev())
        .collect::<String>()
}

#[pyfunction]
pub fn script_to_address(script_pubkey: Vec<u8>, network: &str) -> PyResult<String> {
    // Convert the script pubkey to a Script object
    let script = ScriptBuf::from(script_pubkey);

    // Convert the network string to a Network enum value
    let network_enum = match network {
        "mainnet" => Network::Bitcoin,
        "testnet3" => Network::Testnet,
        "testnet4" => Network::Testnet4,
        "signet" => Network::Signet,
        "regtest" => Network::Regtest,
        _ => {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Invalid network value",
            ))
        }
    };
    if script.is_witness_program() {
        // This block below is necessary to reproduce a prior truncation bug in the python codebase.
        let version = match WitnessVersion::try_from(opcodes::Opcode::from(script.as_bytes()[0])) {
            Ok(vers) => vers,
            Err(_) => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    "Invalid version value",
                ))
            }
        };

        let n = 22;
        if script.len() < n {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Script length is less than 22",
            ));
        }
        let program = WitnessProgram::new(version, &script.as_bytes()[2..n]).map_err(|e| {
            return PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Could not create witness program from script: {}",
                e
            ));
        })?;
        let address = Address::from_witness_program(program, network_enum);
        Ok(address.to_string())
    } else {
        /*
         * the code below is correct, but not sure about the invocation path
         * and untested bug compatibility
         */
        let _address = match Address::from_script(&script, network_enum) {
            Ok(addr) => addr,
            Err(_) => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    "Failed to derive address",
                ))
            }
        };
        panic!("we thought this shouldn't happen!");
        //Ok(address.to_string())
    }
}

#[pyfunction]
pub fn script_to_address2(script_pubkey: Vec<u8>, network: &str) -> PyResult<String> {
    // Convert the script pubkey to a Script object
    let script = ScriptBuf::from(script_pubkey);

    // Convert the network string to a Network enum value
    let network_enum = match network {
        "mainnet" => Network::Bitcoin,
        "testnet3" => Network::Testnet,
        "testnet4" => Network::Testnet4,
        "signet" => Network::Signet,
        "regtest" => Network::Regtest,
        _ => {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Invalid network value",
            ))
        }
    };
    if script.is_witness_program() {
        // This block below is necessary to reproduce a prior truncation bug in the python codebase.
        let version = match WitnessVersion::try_from(opcodes::Opcode::from(script.as_bytes()[0])) {
            Ok(vers) => vers,
            Err(_) => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    "Invalid version value",
                ))
            }
        };

        let n = 22;
        if script.len() < n {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Script length is less than 22",
            ));
        }
        let program = WitnessProgram::new(version, &script.as_bytes()[2..n]).map_err(|e| {
            return PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Could not create witness program from script: {}",
                e
            ));
        })?;
        let address = Address::from_witness_program(program, network_enum);
        Ok(address.to_string())
    } else {
        /*
         * the code below is correct, but not sure about the invocation path
         * and untested bug compatibility
         */
        let address = match Address::from_script(&script, network_enum) {
            Ok(addr) => addr,
            Err(_) => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    "Failed to derive address",
                ))
            }
        };
        Ok(address.to_string())
    }
}

#[pyfunction]
fn script_to_asm(script_bytes: Vec<u8>, py: Python) -> PyResult<Vec<PyObject>> {
    // Wrap the code block that may panic inside `catch_unwind()`
    let result = panic::catch_unwind(|| {
        let script = ScriptBuf::from(script_bytes);

        let mut asm: Vec<PyObject> = Vec::new();

        for instruction in script.instructions() {
            match instruction {
                Ok(instr) => {
                    let py_instruction = match instr {
                        Instruction::Op(op) => opcode_to_bytes(op),
                        Instruction::PushBytes(data) => data.as_bytes().to_vec(),
                    };
                    asm.push(PyBytes::new_bound(py, &py_instruction).into());
                }
                Err(_) => {
                    return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                        "Error processing script",
                    ));
                }
            }
        }

        Ok(asm)
    });

    // Handle the result of `catch_unwind()`
    match result {
        Ok(Ok(value)) => Ok(value), // If there was no panic, return the result
        Ok(Err(err)) => Err(err), // If there was a panic and it returned an error, return that error
        Err(_) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
            "Panic occurred",
        )), // If there was a panic but it didn't return an error, return a custom error
    }
}

fn opcode_to_bytes(opcode: bitcoin::blockdata::opcodes::Opcode) -> Vec<u8> {
    match opcode {
        OP_PUSHBYTES_0 => vec![0x00],
        OP_PUSHBYTES_1 => vec![0x01],
        OP_PUSHBYTES_2 => vec![0x02],
        OP_PUSHBYTES_3 => vec![0x03],
        OP_PUSHBYTES_4 => vec![0x04],
        OP_PUSHBYTES_5 => vec![0x05],
        OP_PUSHBYTES_6 => vec![0x06],
        OP_PUSHBYTES_7 => vec![0x07],
        OP_PUSHBYTES_8 => vec![0x08],
        OP_PUSHBYTES_9 => vec![0x09],
        OP_PUSHBYTES_10 => vec![0x0a],
        OP_PUSHBYTES_11 => vec![0x0b],
        OP_PUSHBYTES_12 => vec![0x0c],
        OP_PUSHBYTES_13 => vec![0x0d],
        OP_PUSHBYTES_14 => vec![0x0e],
        OP_PUSHBYTES_15 => vec![0x0f],
        OP_PUSHBYTES_16 => vec![0x10],
        OP_PUSHBYTES_17 => vec![0x11],
        OP_PUSHBYTES_18 => vec![0x12],
        OP_PUSHBYTES_19 => vec![0x13],
        OP_PUSHBYTES_20 => vec![0x14],
        OP_PUSHBYTES_21 => vec![0x15],
        OP_PUSHBYTES_22 => vec![0x16],
        OP_PUSHBYTES_23 => vec![0x17],
        OP_PUSHBYTES_24 => vec![0x18],
        OP_PUSHBYTES_25 => vec![0x19],
        OP_PUSHBYTES_26 => vec![0x1a],
        OP_PUSHBYTES_27 => vec![0x1b],
        OP_PUSHBYTES_28 => vec![0x1c],
        OP_PUSHBYTES_29 => vec![0x1d],
        OP_PUSHBYTES_30 => vec![0x1e],
        OP_PUSHBYTES_31 => vec![0x1f],
        OP_PUSHBYTES_32 => vec![0x20],
        OP_PUSHBYTES_33 => vec![0x21],
        OP_PUSHBYTES_34 => vec![0x22],
        OP_PUSHBYTES_35 => vec![0x23],
        OP_PUSHBYTES_36 => vec![0x24],
        OP_PUSHBYTES_37 => vec![0x25],
        OP_PUSHBYTES_38 => vec![0x26],
        OP_PUSHBYTES_39 => vec![0x27],
        OP_PUSHBYTES_40 => vec![0x28],
        OP_PUSHBYTES_41 => vec![0x29],
        OP_PUSHBYTES_42 => vec![0x2a],
        OP_PUSHBYTES_43 => vec![0x2b],
        OP_PUSHBYTES_44 => vec![0x2c],
        OP_PUSHBYTES_45 => vec![0x2d],
        OP_PUSHBYTES_46 => vec![0x2e],
        OP_PUSHBYTES_47 => vec![0x2f],
        OP_PUSHBYTES_48 => vec![0x30],
        OP_PUSHBYTES_49 => vec![0x31],
        OP_PUSHBYTES_50 => vec![0x32],
        OP_PUSHBYTES_51 => vec![0x33],
        OP_PUSHBYTES_52 => vec![0x34],
        OP_PUSHBYTES_53 => vec![0x35],
        OP_PUSHBYTES_54 => vec![0x36],
        OP_PUSHBYTES_55 => vec![0x37],
        OP_PUSHBYTES_56 => vec![0x38],
        OP_PUSHBYTES_57 => vec![0x39],
        OP_PUSHBYTES_58 => vec![0x3a],
        OP_PUSHBYTES_59 => vec![0x3b],
        OP_PUSHBYTES_60 => vec![0x3c],
        OP_PUSHBYTES_61 => vec![0x3d],
        OP_PUSHBYTES_62 => vec![0x3e],
        OP_PUSHBYTES_63 => vec![0x3f],
        OP_PUSHBYTES_64 => vec![0x40],
        OP_PUSHBYTES_65 => vec![0x41],
        OP_PUSHBYTES_66 => vec![0x42],
        OP_PUSHBYTES_67 => vec![0x43],
        OP_PUSHBYTES_68 => vec![0x44],
        OP_PUSHBYTES_69 => vec![0x45],
        OP_PUSHBYTES_70 => vec![0x46],
        OP_PUSHBYTES_71 => vec![0x47],
        OP_PUSHBYTES_72 => vec![0x48],
        OP_PUSHBYTES_73 => vec![0x49],
        OP_PUSHBYTES_74 => vec![0x4a],
        OP_PUSHBYTES_75 => vec![0x4b],
        OP_PUSHDATA1 => vec![0x4c],
        OP_PUSHDATA2 => vec![0x4d],
        OP_PUSHDATA4 => vec![0x4e],
        OP_RESERVED => vec![0x50],
        OP_NOP => vec![0x61],
        OP_VER => vec![0x62],
        OP_IF => vec![0x63],
        OP_NOTIF => vec![0x64],
        OP_VERIF => vec![0x65],
        OP_VERNOTIF => vec![0x66],
        OP_ELSE => vec![0x67],
        OP_ENDIF => vec![0x68],
        OP_VERIFY => vec![0x69],
        OP_RETURN => vec![0x6a],
        OP_TOALTSTACK => vec![0x6b],
        OP_FROMALTSTACK => vec![0x6c],
        OP_2DROP => vec![0x6d],
        OP_2DUP => vec![0x6e],
        OP_3DUP => vec![0x6f],
        OP_2OVER => vec![0x70],
        OP_2ROT => vec![0x71],
        OP_2SWAP => vec![0x72],
        OP_IFDUP => vec![0x73],
        OP_DEPTH => vec![0x74],
        OP_DROP => vec![0x75],
        OP_DUP => vec![0x76],
        OP_NIP => vec![0x77],
        OP_OVER => vec![0x78],
        OP_PICK => vec![0x79],
        OP_ROLL => vec![0x7a],
        OP_ROT => vec![0x7b],
        OP_SWAP => vec![0x7c],
        OP_TUCK => vec![0x7d],
        OP_CAT => vec![0x7e],
        OP_SUBSTR => vec![0x7f],
        OP_LEFT => vec![0x80],
        OP_RIGHT => vec![0x81],
        OP_SIZE => vec![0x82],
        OP_INVERT => vec![0x83],
        OP_AND => vec![0x84],
        OP_OR => vec![0x85],
        OP_XOR => vec![0x86],
        OP_EQUAL => vec![0x87],
        OP_EQUALVERIFY => vec![0x88],
        OP_RESERVED1 => vec![0x89],
        OP_RESERVED2 => vec![0x8a],
        OP_1ADD => vec![0x8b],
        OP_1SUB => vec![0x8c],
        OP_2MUL => vec![0x8d],
        OP_2DIV => vec![0x8e],
        OP_NEGATE => vec![0x8f],
        OP_ABS => vec![0x90],
        OP_NOT => vec![0x91],
        OP_0NOTEQUAL => vec![0x92],
        OP_ADD => vec![0x93],
        OP_SUB => vec![0x94],
        OP_MUL => vec![0x95],
        OP_DIV => vec![0x96],
        OP_MOD => vec![0x97],
        OP_LSHIFT => vec![0x98],
        OP_RSHIFT => vec![0x99],
        OP_BOOLAND => vec![0x9a],
        OP_BOOLOR => vec![0x9b],
        OP_NUMEQUAL => vec![0x9c],
        OP_NUMEQUALVERIFY => vec![0x9d],
        OP_NUMNOTEQUAL => vec![0x9e],
        OP_LESSTHAN => vec![0x9f],
        OP_GREATERTHAN => vec![0xa0],
        OP_LESSTHANOREQUAL => vec![0xa1],
        OP_GREATERTHANOREQUAL => vec![0xa2],
        OP_MIN => vec![0xa3],
        OP_MAX => vec![0xa4],
        OP_WITHIN => vec![0xa5],
        OP_RIPEMD160 => vec![0xa6],
        OP_SHA1 => vec![0xa7],
        OP_SHA256 => vec![0xa8],
        OP_HASH160 => vec![0xa9],
        OP_HASH256 => vec![0xaa],
        OP_CODESEPARATOR => vec![0xab],
        OP_CHECKSIG => vec![0xac],
        OP_CHECKSIGVERIFY => vec![0xad],
        OP_CHECKMULTISIG => vec![0xae],
        OP_CHECKMULTISIGVERIFY => vec![0xaf],
        OP_NOP1 => vec![0xb0],
        OP_NOP4 => vec![0xb3],
        OP_NOP5 => vec![0xb4],
        OP_NOP6 => vec![0xb5],
        OP_NOP7 => vec![0xb6],
        OP_NOP8 => vec![0xb7],
        OP_NOP9 => vec![0xb8],
        OP_NOP10 => vec![0xb9],
        OP_INVALIDOPCODE => vec![0xff],
        OP_PUSHNUM_1 => vec![0x01],
        OP_PUSHNUM_2 => vec![0x02],
        OP_PUSHNUM_3 => vec![0x03],
        OP_PUSHNUM_4 => vec![0x04],
        OP_PUSHNUM_5 => vec![0x05],
        OP_PUSHNUM_6 => vec![0x06],
        OP_PUSHNUM_7 => vec![0x07],
        OP_PUSHNUM_8 => vec![0x08],
        OP_PUSHNUM_9 => vec![0x09],
        OP_PUSHNUM_10 => vec![0x0a],
        OP_PUSHNUM_11 => vec![0x0b],
        OP_PUSHNUM_12 => vec![0x0c],
        OP_PUSHNUM_13 => vec![0x0d],
        OP_PUSHNUM_14 => vec![0x0e],
        OP_PUSHNUM_15 => vec![0x0f],
        OP_PUSHNUM_16 => vec![0x10],
        _ => vec![0xff],
    }
}

pub fn register_utils_module(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    let m = PyModule::new_bound(parent_module.py(), "utils")?;
    m.add_function(wrap_pyfunction!(inverse_hash, &m)?)?;
    m.add_function(wrap_pyfunction!(script_to_asm, &m)?)?;
    m.add_function(wrap_pyfunction!(script_to_address, &m)?)?;
    m.add_function(wrap_pyfunction!(script_to_address2, &m)?)?;
    parent_module.add_submodule(&m)?;
    Ok(())
}
