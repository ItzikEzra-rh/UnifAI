# README: Running LLM Finetuning in DDP Mode

This guide explains how to run the **finetuning** for LLM model training in DDP (**Distributed Data Parallel**) mode with 8 nodes. It also includes **WireGuard VPN** setup to ensure secure communication between nodes.

## Table of Contents

1. **Prerequisites**
2. **WireGuard VPN Setup**
3. **Understanding the Training Command**
4. **Running the Training**
5. **Example Configurations**

---

## 1. Prerequisites

Before running the training, ensure you have:

- **8 nodes** (servers or VMs) with GPUs and PyTorch installed.
- **WireGuard** installed for secure communication between nodes.
- Python 3.11 and necessary libraries installed.
- Internet access for downloading model checkpoints and packages.
- Basic understanding of SSH and Linux commands.

---

## 2. WireGuard VPN Setup

To ensure secure communication between nodes, configure **WireGuard** VPN.

### Install WireGuard on Each Node

Run the following command on each node to install **WireGuard**:

```bash
sudo dnf install -y wireguard-tools
```

### Generate Keys

On **each node**, generate the WireGuard private and public keys:

```bash
wg genkey | tee wg_private.key | wg pubkey > wg_public.key
```

- `wg_private.key` is the **private key**.
- `wg_public.key` is the **public key**.

### Configuration File

On each node, create a WireGuard configuration file (`wg0.conf`) in the `/etc/wireguard/` directory:

#### Example Configuration for Node 1 (MASTER NODE)

**File:** `/etc/wireguard/wg0.conf`

```ini
[Interface]
PrivateKey = cM9k9qPZsilyGIEZaQ2QyMjAHpuqxT9CSlMTVwdqV2o=
Address = 10.0.100.1/24
ListenPort = 58895

[Peer]
PublicKey = MVZj7koElYLPeybOevsaP0ELI+CiCwrarHaa3kNgU1U=
AllowedIPs = 10.0.100.2/32
Endpoint = 3.18.238.55:58895
PersistentKeepalive = 25

[Peer]
PublicKey = ahz5NEMfR1jPNb28mZxH6V1nSfl3D7nEeah5tR7lnik=
AllowedIPs = 10.0.100.3/32
Endpoint = 18.220.207.65:58895
PersistentKeepalive = 25
```

Repeat this process for all 8 nodes, changing `PrivateKey`, `Address`, and the peer configurations accordingly.

### Start WireGuard

After creating the configuration file, start WireGuard:

```bash
sudo wg-quick up wg0
```

Verify it is running:

```bash
sudo wg show
```

---

## 3. Understanding the Training Command

The training command uses **torchrun** in DDP mode to distribute training across nodes. Below is a breakdown of the command:

### Training Command

```bash
NCCL_DEBUG=INFO NCCL_SOCKET_IFNAME=wg0 FORCE_TORCHRUN=1 \
NNODES=8 NODE_RANK=7 MASTER_ADDR=10.0.100.1 MASTER_PORT=58895 \
llamafactory-cli train \
    --stage sft \
    --do_train True \
    --model_name_or_path meta-llama/Llama-3.2-3B-Instruct \
    --preprocessing_num_workers 16 \
    --finetuning_type lora \
    --template llama3 \
    --flash_attn auto \
    --dataset_dir data \
    --dataset ecogotest \
    --cutoff_len 1024 \
    --learning_rate 5e-05 \
    --num_train_epochs 5.0 \
    --max_samples 350000 \
    --per_device_train_batch_size 2 \
    --gradient_accumulation_steps 16 \
    --lr_scheduler_type cosine \
    --max_grad_norm 1.0 \
    --logging_steps 5 \
    --save_steps 100 \
    --warmup_steps 0 \
    --report_to none \
    --output_dir saves/Llama-3.2-3B-Instruct/lora/train_YYYY-MM-DD-HH-MM-SS/ \
    --bf16 True \
    --plot_loss True \
    --ddp_timeout 180000000 \
    --optim adamw_torch \
    --lora_rank 32 \
    --lora_alpha 32 \
    --lora_dropout 0 \
    --lora_target all \
    --disable_gradient_checkpointing \
    --ddp_find_unused_parameters False
```

### Important Parameters

- **NCCL_DEBUG=INFO**: Debugging information for the NCCL backend.
- **NCCL_SOCKET_IFNAME=wg0**: Network interface for NCCL communication (use WireGuard `wg0`).
- **NNODES=8**: Total number of nodes.
- **NODE_RANK=7**: Rank of the current node (0-based, i.e., `0-7`).
- **MASTER_ADDR=10.0.100.1**: IP address of the master node.
- **MASTER_PORT=58895**: Port used for communication between nodes.

---

## 4. Running the Training

### Steps to Run Training Across Nodes

1. **Ensure WireGuard is running** on all nodes:

   ```bash
   sudo wg-quick up wg0
   ```

2. **Update the NODE_RANK** for each node.

   - On **Node 0** (Master Node):
     ```bash
     export NODE_RANK=0
     ```
   - On **Node 1**:
     ```bash
     export NODE_RANK=1
     ```
   - Continue this for all nodes up to `NODE_RANK=7`.

3. **Run the Training Command** on each node.
   Replace `NODE_RANK` with the appropriate value for each node and run the command shown above.

4. Monitor logs for progress and errors. Ensure nodes communicate properly.

---

## 5. Example Node Configuration

Here is an example node configuration for clarity:

| **Node** | **IP Address** | **NODE_RANK** | **Private Key** |
| -------- | -------------- | ------------- | --------------- |
| Node 0   | 10.0.100.1     | 0             | cM9k9qPZ...     |
| Node 1   | 10.0.100.2     | 1             | MVZj7koE...     |
| Node 2   | 10.0.100.3     | 2             | ahz5NEMf...     |
| ...      | ...            | ...           | ...             |

---

## Troubleshooting

- **WireGuard Connection Issues:**

   - Check if WireGuard is up:
     ```bash
     sudo wg show
     ```
   - Restart WireGuard:
     ```bash
     sudo wg-quick down wg0 && sudo wg-quick up wg0
     ```

- **NCCL Communication Issues:**

   - Ensure `NCCL_SOCKET_IFNAME` is set to `wg0`.
   - Verify connectivity between nodes:
     ```bash
     ping 10.0.100.x
     ```

- **DDP Timeout Issues:**

   - Increase the `--ddp_timeout` value.

---

## Conclusion

This guide ensures you can configure and finetune LLM model in DDP mode securely and efficiently. If any issues arise, check the troubleshooting section or re-check your WireGuard configuration.

