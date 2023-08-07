# KGTL
# 更新日志

- 2023.06.25,支持gpu选择,例如调用main.py脚本时指定0号gpu`--gpu 0`,修改数据按时间划分的函数,提升数据处理速度
- 2023.06.15,加入过滤功能,外推模型都支持过滤,调用main.py时添加`--filter`参数来进行过滤

# 1 简介
知识图谱工具库包含四个模块——数据模块、工具模块、模型基类模块和模型模块。数据模块包含数据加载类和数据集，工具模块包含一些辅助函数，模型基类模块包含各个模型的基类，基类仅包含初始化和前向传播的过程，训练和评估都集成在模型模块的模型类中。

目前已经集成的模型有：
- [CyGNet](https://ojs.aaai.org/index.php/AAAI/article/view/16604)
- [RGCN](https://dl.acm.org/doi/abs/10.1145/3404835.3462963)
- [CNE](https://arxiv.org/abs/2203.07782)

此外方法库还包含一个可执行main.py脚本，提供了模型训练、评估、保存checkpoint、根据实验数据绘图等功能。

# 2 快速开始

执行以下命令快速训练模型
```
# CyGNet
python main.py \
  --dataset ICEWS14s \
  --model cygnet \
  --epoch 50 \
  --amsgrad \
  --lr 0.001 \
  --early-stop 3
# RE-GCN
python main.py \
  --dataset ICEWS14s \
  --model regcn  \
  --epoch 50 \
  --lr 0.001 \
  --weight-decay 1e-5 \
  --early-stop 3
# CEN
python main.py \
  --dataset ICEWS14s \
  --model cen  \
  --epoch 50 \
  --lr 0.001 \
  --weight-decay 1e-5 \
  --early-stop 3
```
执行以下脚本加载checkpoint在测试集上进行评估
```sh
python main.py \
  --dataset ICEWS14s \
  --model cygnet \
  --test \
  --checkpoint cygnet_ICEWS14s_alpha5e-1_dim50_penalty-100
```
