# Lido CSM validator manager

A CLI tool to deploy, monitor and manage validator keys for the Lido CSM.

## Table of Contents

- [Features](#features)
- [Pre-requisites](#pre-requisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Commands](#commands)

## Features

- Deploy validators: 
  - Create and deploy new validator keys to the validator client and CSM
  - Register a new CSM Node Operator if needed
  - Duplicate validator key checks at the validator client, remote signer and CSM level
  - Optionally, upload keystores to a remote signer
- Manage validator keys: 
  - Find inconsistencies between keys registered in the validator client, remote signer and CSM
  - Rollback of inconsistent states
- Exit validators:
  - Manually, with its public key
  - Automatically, by monitoring the Lido Validator Exit Bus Oracle and actioning exit requests
  - Telegram notifications for detected exit requests
- Relay check:
  - Check if the validator keys are registered with all whitelisted relays in the Lido Relay Allowlist contract
- Support for remote signer setups (e.g. web3signer)

## Pre-requisites

- Python (>=3.12 recommended) or Docker
- The [deposit key generation tool](https://github.com/ethereum/staking-deposit-cli)
  - Not needed if using Docker script
- A previously generated seed phrase compliant with the deposit tool's requirements
- Access to a synchronized, running Ethereum RPC node (EL & CL)
  - Reachable through HTTP & WS (CL & EL respectively)
- A running validator client with support for mutiple key management (e.g. Lighthouse)
  - With active Keymanager API listening in localhost
  - Reachable through SSH

## Setup

The tool can be run either with Python or Docker.

### Python

Install python dependencies:

```
pip install -r requirements.txt
```

If you have issues with installing the dependencies or running the tool, consider setting up a virtual environment beforehand:

```
python -m venv .venv
source .venv/bin/activate
```

You can then run the tool with:

```
python -m swarm <command>
```

See the [Commands](#commands) section for more details.

### Docker

You can also run the tool with Docker, like this:

```
./swarm.sh <command>
```

See the [Commands](#commands) section for more details.

If you make changes to your configuration file, or any other environment files (i.e. your local ssh directory), you will need to rebuild the Docker image, like this:

```
./swarm.sh docker-rebuild
```

If you want to enter the Docker container shell, you can do so with:

```
./swarm.sh shell
```

### Configuration file

Copy `config.toml.holesky.example` or `config.toml.mainnet.example` to `config.toml` and fill with your configuration values

```
cp config.toml.holesky.example config.toml
```

The Holesky config file may contain:

```toml
eth_base="<YOUR OPERATOR WALLET ADDRESS>"
chain="holesky"

[deposit]
path="/path/to/deposit/tool/deposit/"

[csm]
node_operator_id=999999

[rpc]
execution_address="ws://my-exec-rpc-address:port"
consensus_address="http://my-beacon-rpc-address:port"

[validator_api]
auth_token="api-token-0x123456789"
ssh_address="user@server"
port=5062

[remote_signer]
ssh_address="user@signer"
port=9000
url="http://my-remote-signer.xyz:port"

[monitoring]
node_operator_ids = [420, 666]

[telegram]
bot_token = 'xxxxxxxx-telegram-bot-token'
channel_id = '-123456'
```

Some of these parameters are optional and can be omitted depending on the functionality you want to use. See the next section for more details.

## Configuration

The configuration file contains the following parameters:

### General

- `eth_base`: The operator wallet address used for submitting transactions. Only required for registering new node operators or validator keys to the CSM.
- `chain`: The Ethereum network to use (e.g. "mainnet", "holesky"). Always required.

### Deposit Configuration

Only required for deploying validators.
 
- `path`: Path to the deposit tool binary.

### CSM (Community Staking Module) Configuration  

Required for deploying validators and checking relay registrations.

- `node_operator_id`: Your assigned node operator ID in the CSM protocol.

### RPC Endpoints

- `execution_address`: WebSocket URL for execution layer RPC. Required for interacting with the CSM (i.e. registering new node operators or validator keys, state checks, or monitoring the Validator Exit Bus Oracle).
- `consensus_address`: HTTP URL for consensus layer RPC. Required for broadcasting validator exits.

### Validator API Configuration

Required for interacting with the validator client (i.e. submitting validator keys, or signing validator exits).

- `auth_token`: Authentication token for validator API access.
- `ssh_address`: SSH address for validator client access
- `port`: Port number for validator API

### Remote Signer Configuration

Only for setups where the validator keys are stored in a remote signer.

- `ssh_address`: SSH address for remote signer access
- `port`: Port number for remote signer
- `url`: HTTP URL for remote signer API

### Monitoring Configuration

Only required for state checks and automated exits, not for deploying validators.

- `node_operator_ids`: List of one or more node operator IDs to monitor for exit requests

### Telegram Configuration

Only required for receiving validator exit notifications via Telegram.

- `bot_token`: Telegram bot token
- `channel_id`: Telegram channel ID

## Commands

The commands below are the same for both Python and Docker. The Python command is prefixed with `python -m swarm`, while the Docker command is prefixed with `./swarm.sh`.

### Deploying validators 

`deploy --n_keys <N> --index <I> [--remote_sign]`

`N` is the number of keys to be generated and submitted, and `I` is the starting index for key generation, defaults to 0.

The `--remote_sign` flag indicates that the keystores will be uploaded to a remote signer, while also registered as remote keys in the configured validator. Otherwise, the keystores will be stored in the validator client.

This action will create a Node Operator in the CSM if the address is not already registered. Otherwise, the generated validator keys will be registered to the configured Node Operator.

### State check

The state check subcommand will retrieve all keys registered in CSM, validator client, and remote signer, and check for inconsistencies.

`state-check [--delete]`

`--delete` will attempt to remove dangling validator keys, i.e. validator keys that are present either in the validaor client or remote signer, but not in CSM. Keys registered in CSM will never be deleted.

### Relay check

The relay check subcommand will check if the validator keys are registered with all whitelisted relays in the Lido Relay Allowlist.

`relay-check [--detailed] [--pubkey <pubkey>]`

The `--detailed` flag will print a more detailed report with specific relay URLs per validator.

The `--pubkey` flag allows checking a specific validator, showing a detailed report for just that validator.

### Manual exit

This subcommand will submit an exit request for a validator with a given public key.

`exit --pubkey <pubkey>`

`pubkey` is the public key of the validator to be exited.

### Monitoring and automated exits

This subcommand will monitor the Lido Validator Exit Bus Oracle and log exit requests for the configured node operator ids.

`auto_exit [--delete] [--telegram]`

The `--delete` flag indicates that the validator will be automatically exited when an exit request has been detected.

The `--telegram` flag indicates that the exit request will be relayed to a Telegram channel.