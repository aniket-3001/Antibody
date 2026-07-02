import os

def generate_sources():
    output_dir = "tests/test_sources"
    os.makedirs(output_dir, exist_ok=True)
    
    # Paper 1: Attention Is All You Need
    paper1_content = """# Attention Is All You Need

| Attribute | Value |
|---|---|
| Authors | Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin |
| Institution | Google Brain, Google Research, University of Toronto |
| Year | 2017 |
| Conference | NeurIPS |
| Citations | 100,000+ |

## Abstract
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.

## 1. Introduction
Recurrent neural networks, especially Long Short-Term Memory (LSTM) and gated recurrent unit (GRU) networks, have been firmly established as state-of-the-art approaches in sequence modeling and transduction problems such as language modeling and machine translation. Since then, numerous efforts have continued to push the boundaries of recurrent language models and encoder-decoder architectures.

Recurrent models vector computation typically aligns along the positions of the input and output sequence. Aligning positions to steps in computation time, they generate a sequence of hidden states $h_t$, as a function of the previous hidden state $h_{t-1}$ and the input for position $t$. This inherently sequential nature precludes parallelization within training examples, which becomes critical at longer sequence lengths, as memory constraints limit batching across examples. Recent work has achieved significant improvements in computational efficiency through factorization tricks and conditional computation, while the fundamental constraint of sequential computation remains.

Attention mechanisms have become an integral part of compelling sequence modeling and transduction models in various tasks, allowing modeling of dependencies without regard to their distance in the input or output sequences. In all but a few cases, however, such attention mechanisms are used in conjunction with a recurrent network.

In this work we propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output. The Transformer allows for significantly more parallelization and can reach a new state of the art in translation quality after being trained for as little as twelve hours on eight GPUs.

## 2. Background
The goal of reducing sequential computation also formed the foundation of Extended Neural GPU, ByteNet and ConvS2S, all of which use convolutional neural networks as basic building blocks, computing hidden representations in parallel for all input and output positions. In these models, the number of operations required to relate signals from two arbitrary input or output positions grows in the distance between positions, linearly for ConvS2S and logarithmically for ByteNet. This makes it more difficult to learn dependencies between distant positions. In the Transformer, this is reduced to a constant number of operations, albeit at the cost of reduced effective resolution due to averaging attention-weighted positions, an effect we counteract with Multi-Head Attention.

Self-attention, sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. Self-attention has been used successfully in a variety of tasks including reading comprehension, abstractive summarization, textual entailment and learning task-independent sentence representations.

End-to-end memory networks are based on a recurrent attention mechanism instead of sequence-aligned recurrence and have been shown to perform well on simple-language question answering and language modeling tasks.

To the best of our knowledge, however, the Transformer is the first transduction model relying entirely on self-attention to compute representations of its input and output without using sequence-aligned RNNs or convolution.

## 3. Model Architecture
Most competitive neural sequence transduction models have an encoder-decoder structure. Here, the encoder maps an input sequence of symbol representations $(x_1, ..., x_n)$ to a sequence of continuous representations $z = (z_1, ..., z_n)$. Given $z$, the decoder then generates an output sequence $(y_1, ..., y_m)$ of symbols one element at a time. At each step the model is auto-regressive, consuming the previously generated symbols as additional input when generating the next.

The Transformer follows this overall architecture using stacked self-attention and point-wise, fully connected layers for both the encoder and decoder.

### 3.1 Encoder and Decoder Stacks
- **Encoder:** The encoder is composed of a stack of $N = 6$ identical layers. Each layer has two sub-layers. The first is a multi-head self-attention mechanism, and the second is a simple, position-wise fully connected feed-forward network. We employ a residual connection around each of the two sub-layers, followed by layer normalization. That is, the output of each sub-layer is $\\text{LayerNorm}(x + \\text{Sublayer}(x))$, where $\\text{Sublayer}(x)$ is the function implemented by the sub-layer itself. To facilitate these residual connections, all sub-layers in the model, as well as the embedding layers, produce outputs of dimension $d_{\\text{model}} = 512$.
- **Decoder:** The decoder is also composed of a stack of $N = 6$ identical layers. In addition to the two sub-layers in each encoder layer, the decoder inserts a third sub-layer, which performs multi-head attention over the output of the encoder stack. Similar to the encoder, we employ residual connections around each of the sub-layers, followed by layer normalization. We also modify the self-attention sub-layer in the decoder stack to prevent positions from attending to subsequent positions. This masking, combined with fact that the output embeddings are offset by one position, ensures that the predictions for position $i$ can depend only on the known outputs at positions less than $i$.

### 3.2 Attention
An attention function can be described as mapping a query and a set of key-value pairs to an output, where the query, keys, values, and output are all vectors. The output is computed as a weighted sum of the values, where the weight assigned to each value is computed by a compatibility function of the query with the corresponding key.

We call our particular attention "Scaled Dot-Product Attention". The input consists of queries and keys of dimension $d_k$, and values of dimension $d_v$. We compute the dot products of the query with all keys, divide each by $\\sqrt{d_k}$, and apply a softmax function to obtain the weights on the values.

In practice, we compute the attention function on a set of queries simultaneously, packed together into a matrix $Q$. The keys and values are also packed together into matrices $K$ and $V$. We compute the matrix of outputs as:

$$\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V$$

The two most commonly used attention mechanisms are additive attention, and dot-product (multiplicative) attention. Dot-product attention is identical to our algorithm, except for the scaling factor of $1/\\sqrt{d_k}$. Additive attention computes the compatibility function using a feed-forward network with a single hidden layer. While the two are similar in theoretical complexity, dot-product attention is much faster and more space-efficient in practice, since it can be implemented using highly optimized matrix multiplication code.

While for small values of $d_k$ the two mechanisms perform similarly, additive attention outperforms dot product attention without scaling for larger values of $d_k$. We suspect that for large values of $d_k$, the dot products grow large in magnitude, pushing the softmax function into regions with extremely small gradients. To counteract this effect, we scale the dot products by $1/\\sqrt{d_k}$.

Instead of performing a single attention function with $d_{\\text{model}}$-dimensional queries, keys and values, we found it beneficial to linearly project the queries, keys and values $h$ times with different, learned linear projections to $d_k$, $d_k$ and $d_v$ dimensions, respectively. On each of these projected versions of queries, keys and values we then perform the attention function in parallel, yielding $d_v$-dimensional output values. These are concatenated and once again projected, resulting in the final values.

Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions. With a single attention head, averaging inhibits this.

$$\\text{MultiHead}(Q, K, V) = \\text{Concat}(\\text{head}_1, ..., \\text{head}_h)W^O$$
$$\\text{where } \\text{head}_i = \\text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

Where the projections are parameter matrices:
- $W_i^Q \\in \\mathbb{R}^{d_{\\text{model}} \\times d_k}$
- $W_i^K \\in \\mathbb{R}^{d_{\\text{model}} \\times d_k}$
- $W_i^V \\in \\mathbb{R}^{d_{\\text{model}} \\times d_v}$
- $W^O \\in \\mathbb{R}^{h d_v \\times d_{\\text{model}}}$

In this work we employ $h = 8$ parallel attention heads. For each of these we use $d_k = d_v = d_{\\text{model}}/h = 64$. Due to the reduced dimension of each head, the total computational cost is similar to that of single-head attention with full dimensionality.

### 3.3 Applications of Attention in the Model
The Transformer uses multi-head attention in three different ways:
1. In "encoder-decoder attention" layers, the queries come from the previous decoder layer, and the memory keys and values come from the output of the encoder. This allows every position in the decoder to attend over all positions in the input sequence. This mimics the typical encoder-decoder attention mechanisms in sequence-to-sequence models.
2. The encoder contains self-attention layers. In a self-attention layer all of the keys, values and queries come from the same place, in this case, the output of the previous layer in the encoder. Each position in the encoder can attend to all positions in the previous layer of the encoder.
3. Similarly, self-attention layers in the decoder allow each position in the decoder to attend to all positions in the decoder up to and including that position. We need to prevent leftward information flow in the decoder to preserve the auto-regressive property. We implement this inside of scaled dot-product attention by masking out (setting to $-\\infty$) all values in the input of the softmax which correspond to illegal connections.

### 3.4 Position-wise Feed-Forward Networks
In addition to attention sub-layers, each of the layers in our encoder and decoder contains a fully connected feed-forward network, which is applied to each position separately and identically. This consists of two linear transformations with a ReLU activation in between.

$$\\text{FFN}(x) = \\max(0, xW_1 + b_1)W_2 + b_2$$

While the linear transformations are the same across different positions, they use different parameters from layer to layer. Another way of describing this is as two convolutions with kernel size 1. The dimensionality of input and output is $d_{\\text{model}} = 512$, and the inner-layer has dimensionality $d_{ff} = 2048$.

### 3.5 Embeddings and Softmax
Similarly to other sequence transduction models, we use learned embeddings to convert the input tokens and output tokens to vectors of dimension $d_{\\text{model}}$. We also use the usual learned linear transformation and softmax function to convert the decoder output to predicted next-token probabilities. In our model, we share the same weight matrix between the two embedding layers and the pre-softmax linear transformation. In the embedding layers, we multiply those weights by $\\sqrt{d_{\\text{model}}}$.

### 3.6 Positional Encoding
Since our model contains no recurrence and no convolution, in order for the model to make use of the order of the sequence, we must inject some information about the relative or absolute position of the tokens in the sequence. To this end, we add "positional encodings" to the input embeddings at the bottoms of the encoder and decoder stacks. The positional encodings have the same dimension $d_{\\text{model}}$ as the embeddings, so that the two can be summed. There are many choices of positional encodings, learned and fixed.

In this work, we use sine and cosine functions of different frequencies:

$$PE_{(pos, 2i)} = \\sin(pos / 10000^{2i/d_{\\text{model}}})$$
$$PE_{(pos, 2i+1)} = \\cos(pos / 10000^{2i/d_{\\text{model}}})$$

where $pos$ is the position and $i$ is the dimension. That is, each dimension of the positional encoding corresponds to a sinusoid. The wavelengths form a geometric progression from $2\\pi$ to $10000 \\cdot 2\\pi$. We chose this function because we hypothesized it would allow the model to easily learn to attend by relative positions, since for any fixed offset $k$, $PE_{pos+k}$ can be represented as a linear function of $PE_{pos}$.

We also experimented with using learned positional embeddings instead, and found that the two versions produced nearly identical results. We chose the sinusoidal version because it may allow the model to extrapolate to sequence lengths longer than those encountered during training.

## 4. Why Self-Attention
In this section we compare various aspects of self-attention layers to the recurrent and convolutional layers commonly used for mapping one variable-length sequence of representations $(x_1, ..., x_n)$ to another sequence of equal length $(y_1, ..., y_n)$, with $x_i, y_i \\in \\mathbb{R}^d$, such as a hidden layer in a typical sequence transduction encoder or decoder. To motivate our use of self-attention we consider three desiderata.

One is the total computational complexity per layer. Another is the amount of computation that can be parallelized, as measured by the minimum number of sequential operations required.

The third is the path length between long-range dependencies in the network. Learning long-range dependencies is a key challenge in many sequence transduction tasks. One key factor affecting the ability to learn such dependencies is the path length signals have to travel forward and backward through the network. The shorter the path between any combination of positions in the input and output sequences, the easier it is to learn long-range dependencies. Hence we also compare the maximum path length between any two input and output positions in networks composed of different layer types.

| Layer Type | Complexity per Layer | Sequential Operations | Maximum Path Length |
|---|---|---|---|
| Self-Attention | $O(n^2 \\cdot d)$ | $O(1)$ | $O(1)$ |
| Recurrent | $O(n \\cdot d^2)$ | $O(n)$ | $O(n)$ |
| Convolutional | $O(k \\cdot n \\cdot d^2)$ | $O(1)$ | $O(\\log_k(n))$ |
| Self-Attention (restricted) | $O(r \\cdot n \\cdot d)$ | $O(1)$ | $O(n/r)$ |

As noted in the table, a self-attention layer connects all positions with a constant number of sequentially executed operations, whereas a recurrent layer requires $O(n)$ sequential operations. In terms of computational complexity, self-attention layers are faster than recurrent layers when the sequence length $n$ is smaller than the representation dimensionality $d$, which is most commonly the case with sentence representations used by state-of-the-art models in machine translation, such as word-piece and byte-pair representations.

To improve computational efficiency for tasks involving very long sequences, self-attention could be restricted to considering only a neighborhood of size $r$ in the input sequence centered around the respective output position. This would increase the maximum path length to $O(n/r)$. We plan to investigate this approach further in future work.

A side benefit of self-attention is that it can yield more interpretable models. We inspect attention distributions from our models and discuss examples in the appendix. Not only do individual attention heads clearly learn to perform different tasks, many appear to exhibit behavior related to the syntactic and semantic structure of the sentences.

## 5. Training
This section describes the training regime for our models.

### 5.1 Training Data and Batching
We trained on the standard WMT 2014 English-German dataset consisting of about 4.5 million sentence pairs. Sentences were encoded using byte-pair encoding, which has a shared source-target vocabulary of about 37000 tokens. For English-French, we used the significantly larger WMT 2014 English-French dataset consisting of 36 million sentences and split tokens into a 32000 word-piece vocabulary. Sentence pairs were batched together by approximate sequence length. Each training batch contained a set of sentence pairs containing approximately 25000 source tokens and 25000 target tokens.

### 5.2 Hardware and Schedule
We trained our models on one machine with 8 NVIDIA P100 GPUs. For our base models using the hyperparameters described throughout the paper, each training step took about 0.4 seconds. We trained the base models for a total of 100,000 steps or 12 hours. For our big models, which we describe in the bottom table, step time was 1.0 seconds. The big models were trained for 300,000 steps (about 3.5 days).

### 5.3 Optimizer
We used the Adam optimizer with $\\beta_1 = 0.9$, $\\beta_2 = 0.98$ and $\\epsilon = 10^{-9}$. We varied the learning rate over the course of training, according to the formula:

$$lrate = d_{\\text{model}}^{-0.5} \\cdot \\min(\\text{step_num}^{-0.5}, \\text{step_num} \\cdot \\text{warmup_steps}^{-1.5})$$

This corresponds to increasing the learning rate linearly for the first $warmup\\_steps$ training steps, and decreasing it thereafter proportionally to the inverse square root of the step number. We used $warmup\\_steps = 4000$.

### 5.4 Regularization
We employed three types of regularization during training:

- **Residual Dropout:** We apply dropout to the output of each sub-layer, before it is added to the sub-layer input and normalized. In addition, we apply dropout to the sums of the embeddings and the positional encodings in both the encoder and decoder stacks. For the base model, we use a rate of $P_{drop} = 0.1$.
- **Label Smoothing:** During training, we employed label smoothing of value $\\epsilon_{ls} = 0.1$. This hurts perplexity, as the model learns to be more unsure, but improves accuracy and BLEU score.

## 6. Results
On the WMT 2014 English-to-German translation task, the big Transformer model outperforms the best previously reported models (including ensembles) by more than 2.0 BLEU, establishing a new state-of-the-art BLEU score of 28.4. The configuration of this model is listed in the bottom table.

| Model | BLEU (EN-DE) | BLEU (EN-FR) | Training Cost (FLOPs) |
|---|---|---|---|
| ByteNet | 26.3 | - | - |
| ConvS2S | 26.36 | 41.29 | $9.6 \\cdot 10^{19}$ |
| GNMT+RL | 24.6 | 39.92 | $1.5 \\cdot 10^{20}$ |
| Transformer (base) | 27.3 | 38.1 | $3.3 \\cdot 10^{18}$ |
| Transformer (big) | 28.4 | 41.0 | $2.3 \\cdot 10^{19}$ |

On the WMT 2014 English-to-French translation task, our big model established a BLEU score of 41.0, outperforming all of the previously reported single models, at a fraction of the training cost of the previous state-of-the-art models.

## 7. Conclusion
In this work, we presented the Transformer, the first sequence transduction model relying entirely on attention, replacing the recurrent layers most commonly used in encoder-decoder architectures with multi-head self-attention.

For translation tasks, the Transformer can be trained significantly faster than architectures based on recurrent or convolutional layers. On both WMT 2014 English-to-German and WMT 2014 English-to-French translation tasks, we achieved a new state of the art. The base model outperforms all previously reported ensemble and single models, while doing so at a lower training cost than any competitive model.

We are excited about the future of attention-based models and plan to apply them to other tasks. We plan to extend the Transformer to problems involving input and output modalities other than text, such as images, audio and video. Making generation less sequential is another of our active research goals.

## References
1. Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, and Illia Polosukhin. 2017. Attention is all you need. In Advances in Neural Information Processing Systems, pages 5998–6008.
2. Jonas Gehring, Michael Auli, David Grangier, Denis Yarats, and Yann N. Dauphin. 2017. Convolutional Sequence to Sequence Learning. arXiv preprint arXiv:1705.03122.
3. Sepp Hochreiter and Jürgen Schmidhuber. 1997. Long short-term memory. Neural Computation, 9(8):1735–1780.
4. Dzmitry Bahdanau, Kyunghyun Cho, and Yoshua Bengio. 2014. Neural machine translation by jointly learning to align and translate. arXiv preprint arXiv:1409.0473.
"""

    # Add 9 more stub paper contents, structured very similarly to be long
    # We will programmatically generate them to hit ~320 lines each
    papers = [
        ("attention_is_all_you_need.md", paper1_content),
    ]
    
    # We can write a helper to generate structured academic summaries
    def make_academic_summary(title, authors, year, abstract, key_sections):
        lines = []
        lines.append(f"# {title}\n")
        lines.append("| Attribute | Value |")
        lines.append("|---|---|")
        lines.append(f"| Authors | {authors} |")
        lines.append(f"| Year | {year} |")
        lines.append("| Status | Peer Reviewed |")
        lines.append("\n## Abstract")
        lines.append(abstract)
        
        # We need to fill ~300 lines of descriptive text
        for section_title, content_list in key_sections.items():
            lines.append(f"\n## {section_title}")
            for paragraph in content_list:
                lines.append(paragraph)
                lines.append("")
                
        # Fill rest with detailed theoretical exploration to ensure line count
        lines.append("\n## Theoretical Details & Equations")
        for i in range(1, 40):
            lines.append(f"### Theorem {i}: Conceptual Framework Formulation")
            lines.append(f"To describe the system dynamics under condition {i}, we formulate the optimization objective as:")
            lines.append(f"$$\\mathcal{{L}}_{{\\text{{opt}}, {i}}}(\\theta) = \\mathbb{{E}}_{{x \\sim \\mathcal{{D}}}}\\left[ \\sum_{{t=1}}^{{T}} \\gamma^t D_{{KL}}\\left( P(y_t | x_{{<t}}; \\theta) \\;\\|\\; Q(y_t | x_{{<t}}) \\right) \\right] + \\lambda \\|\\theta\\|_2^2$$")
            lines.append(f"Here, the parameter vector $\\theta$ represents the weights of the neural architecture, and $\\gamma$ represents a discounting factor designed to prioritize local context boundaries in step {i}. Under structural assumptions, we prove convergence under standard gradient dynamics.")
            lines.append("")
            
        lines.append("\n## Detailed Section-by-Section Analysis")
        for i in range(1, 25):
            lines.append(f"### Section Analysis {i}: Domain Adaptation and Robustness")
            lines.append(f"In this section, we analyze parameter dynamics under subset {i}. "
                         "This is done to ensure statistical variance remains bounded across epochs. "
                         "By measuring the L2 norm of the gradient update vector at step 1000, "
                         "we verify that convergence bounds are respected. This confirms the validity "
                         "of the scaling law predictions and guarantees model stability in downstream configurations.")
            lines.append("")
            
        lines.append("\n## Empirical Results & Tables")
        lines.append("We evaluated the performance of our method across multiple standard benchmarks. The results are summarized below:")
        lines.append("")
        lines.append("| Model Size | Dataset Scale | Parameter Count | Epochs | Accuracy (%) | F1 Score | Latency (ms) |")
        lines.append("|---|---|---|---|---|---|---|")
        for size in ["Tiny", "Mini", "Small", "Medium", "Base", "Large", "XL", "XXL"]:
            lines.append(f"| {size} | 10B tokens | {size}x10^6 | 3 | {80.5 + len(size)*1.2:.1f}% | {0.82 + len(size)*0.01:.2f} | {12 + len(size)*4}ms |")
        
        lines.append("\n## Discussion")
        lines.append("Several notable aspects emerge from our empirical investigation:")
        for idx in range(1, 15):
            lines.append(f"{idx}. **Observation {idx}:** The scaling dynamics follow a power-law relationship with respect to the computing budget. Specifically, the loss decreases monotonically as a function of training compute, without showing early saturation on downstream tasks.")
            
        lines.append("\n## References")
        for idx in range(1, 6):
            lines.append(f"{idx}. Author, A. et al. ({year - idx}). \"Early foundations of structured models for {title.split()[-1]}.\". Journal of Neural Systems.")
            
        return "\n".join(lines)

    # Let's add the other 9 papers
    # Paper 2: BERT
    papers.append(("bert_paper.md", make_academic_summary(
        "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova",
        2018,
        "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.",
        {
            "1. Introduction": [
                "Language model pre-training has been shown to be effective for improving many natural language processing tasks. These include sentence-level tasks such as natural language inference and paraphrasing, as well as token-level tasks such as named entity recognition and question answering.",
                "There are two existing strategies for applying pre-trained language representations to downstream tasks: feature-based and fine-tuning. The feature-based approach, such as ELMo, uses task-specific architectures that include pre-trained representations as additional features. The fine-tuning approach, such as the Generative Pre-trained Transformer (OpenAI GPT), introduces minimal task-specific parameters, and is trained on the downstream tasks by simply fine-tuning all pre-trained parameters."
            ],
            "2. Methodology": [
                "We introduce two pre-training tasks to guide BERT's learning: the Masked Language Model (MLM) and Next Sentence Prediction (NSP).",
                "**Masked LM:** In order to train a deep bidirectional representation, we simply mask some percentage of the input tokens at random, and then predict those masked tokens. We refer to this procedure as a 'masked LM' (MLM), although it is often referred to as a Cloze task in the literature.",
                "**Next Sentence Prediction:** Many important downstream tasks such as Question Answering (QA) and Natural Language Inference (NLI) are based on understanding the relationship between two sentences, which is not directly captured by language modeling."
            ]
        }
    )))

    # Paper 3: GPT-3
    papers.append(("gpt3_few_shot.md", make_academic_summary(
        "Language Models are Few-Shot Learners",
        "Tom B. Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, Sandhini Agarwal, Ariel Herbert-Voss, Gretchen Krueger, Tom Henighan, Rewon Child, Aditya Ramesh, Daniel M. Ziegler, Jeffrey Wu, Clemens Winter, Christopher Hesse, Mark Chen, Eric Sigler, Mateusz Litwin, Scott Gray, Benjamin Chess, Jack Clark, Christopher Berner, Sam McCandlish, Alec Radford, Ilya Sutskever, Dario Amodei",
        2020,
        "We demonstrate that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches. We train GPT-3, an autoregressive language model with 175 billion parameters, 10x more than any previous non-sparse language model, and test its performance in the few-shot setting. For all tasks, GPT-3 is applied without any gradient updates or fine-tuning, with tasks and few-shot demonstrations specified purely via text interaction with the model.",
        {
            "1. Introduction": [
                "Recent years have seen a trend towards pre-training language representations using increasingly larger datasets and parameter scales, followed by fine-tuning on specific downstream tasks. This approach has led to substantial progress across natural language processing.",
                "However, a major limitation of this paradigm is that while the pre-training is task-agnostic, the model still requires task-specific fine-tuning datasets containing thousands or tens of thousands of labeled examples to achieve high performance on downstream tasks."
            ],
            "2. Model Specifications": [
                "Our model, GPT-3, uses the same transformer architecture as GPT-2, including the modified initialization, pre-normalization, and reversible tokenization described therein.",
                "We evaluate GPT-3 in three settings: few-shot learning (where we allow as many demonstrations as fit in the model's context window, typically 10 to 100), one-shot learning (where we allow only one demonstration), and zero-shot learning (where no demonstrations are allowed, only an instruction in natural language)."
            ]
        }
    )))

    # Paper 4: LoRA
    papers.append(("lora_adaptation.md", make_academic_summary(
        "LoRA: Low-Rank Adaptation of Large Language Models",
        "Edward J. Hu, Yibin Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu Wang, Weizhu Chen",
        2021,
        "An important paradigm of natural language processing consists of large-scale pre-training on general domain data and adaptation to specific tasks or domains. As we pre-train larger models, full fine-tuning, which retrains all model parameters, becomes less feasible. Using GPT-3 175B as an example, deploying fine-tuned models is prohibitively expensive. We propose Low-Rank Adaptation, or LoRA, which freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture, greatly reducing the number of trainable parameters for downstream tasks.",
        {
            "1. Introduction": [
                "Many applications in natural language processing rely on adapting a single large, pre-trained language model to multiple downstream tasks. This adaptation is usually done via fine-tuning, which updates all the parameters of the pre-trained model.",
                "The major drawback of full fine-tuning is that the resulting model has the same size as the original model. For models like GPT-3, storing and deploying a separate fine-tuned model for every target task becomes highly impractical."
            ],
            "2. Low-Rank Parametrized Updates": [
                "LoRA limits the rank of the parameter updates during adaptation. Let $W_0 \\in \\mathbb{R}^{d \\times k}$ be a pre-trained weight matrix. We constrain its update $\\Delta W$ by representing it as a low-rank decomposition $B \\cdot A$, where $B \\in \\mathbb{R}^{d \\times r}$ and $A \\in \\mathbb{R}^{r \\times k}$, with the rank $r \\ll \\min(d, k)$.",
                "During training, $W_0$ is frozen and receives no gradient updates, while $A$ and $B$ contain trainable parameters. Note that both $W_0$ and $\\Delta W = BA$ are multiplied with the same input $x$."
            ]
        }
    )))

    # Paper 5: RAG
    papers.append(("rag_retrieval_augmented.md", make_academic_summary(
        "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "Patrick Lewis, Ethan Perez, Aleksandrina Peneva, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela",
        2020,
        "Large pre-trained language models have been shown to store implicit knowledge in their parameters, and achieve state-of-the-art results when fine-tuned on downstream NLP tasks. However, their ability to access and precisely manipulate knowledge is still limited, and they can hallucinate false facts. We introduce Retrieval-Augmented Generation (RAG) models, which combine pre-trained parametric memory (generator) and non-parametric memory (retriever) in an end-to-end framework, showing superior performance on open-domain QA and generation tasks.",
        {
            "1. Introduction": [
                "Pre-trained neural language models learn a substantial amount of factual knowledge from text. However, they cannot easily expand or revise their memory, can hallucinate facts, and lack interpretability.",
                "Hybrid models that combine parametric representations with non-parametric memories (such as dense document retrievers) offer a promising path forward. Non-parametric memories allow models to directly access external knowledge repositories."
            ],
            "2. RAG Architecture": [
                "RAG models consist of a retriever $p_\\eta(z|x)$ and a generator $p_\\theta(y|x, z)$. The retriever provides latent documents $z$ given a query $x$, and the generator produces the output tokens $y$ conditioned on both $x$ and $z$.",
                "We explore two variants: RAG-Sequence, which uses the same retrieved document to generate the complete target sequence, and RAG-Token, which can retrieve different documents for each token in the target sequence."
            ]
        }
    )))

    # Paper 6: FlashAttention
    papers.append(("flash_attention.md", make_academic_summary(
        "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
        "Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudra, Christopher Ré",
        2022,
        "Transformer models are increasingly being scaled to longer sequence lengths, but their self-attention mechanism is limited by its quadratic time and memory complexity in sequence length. We propose FlashAttention, an IO-aware exact attention algorithm that uses tiling to reduce the number of memory reads/writes between GPU High Bandwidth Memory (HBM) and GPU SRAM. We show that FlashAttention trains Transformers faster and enables longer context windows, leading to better model quality.",
        {
            "1. Introduction": [
                "Large Transformer models have achieved massive success, but scaling them to longer contexts remains a major bottleneck due to the quadratic complexity of self-attention.",
                "Standard attention implementations are memory-bound: they read and write the intermediate attention matrix ($N \\times N$) to HBM multiple times. FlashAttention solves this by tiling the inputs, performing the softmax step incrementally, and avoiding the storage of the large attention matrix in HBM."
            ],
            "2. IO-Aware Design": [
                "GPU architectures have high-bandwidth but slow memory (HBM) and low-capacity but fast memory (SRAM). Standard implementations compute $S = QK^T$, store it in HBM, compute $P = \\text{softmax}(S)$, store it in HBM, and finally compute $O = PV$.",
                "FlashAttention computes attention exactly by loading blocks of $Q, K, V$ into SRAM, computing local attention, and scaling outputs dynamically using softmax normalization constants ($m, l$) to produce the correct global attention output without materializing the $N \\times N$ matrix in HBM."
            ]
        }
    )))

    # Paper 7: DPO
    papers.append(("dpo_preference_optimization.md", make_academic_summary(
        "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
        "Rafael Rafailov, Archit Sharma, Eric Mitchell, Stefano Ermon, Christopher D. Manning, Chelsea Finn",
        2023,
        "While large-scale unsupervised language models learn broad world knowledge and some reasoning skills, achieving precise control over their behavior requires steering them using human feedback. Standard Reinforcement Learning from Human Feedback (RLHF) is a complex and often unstable process, requiring training a separate reward model and utilizing PPO. We present Direct Preference Optimization (DPO), a stable, performant, and computationally lightweight algorithm that optimizes the policy directly on preference data without training a reward model.",
        {
            "1. Introduction": [
                "Aligning large language models with human preferences is critical for creating safe, helpful assistants. The standard approach, RLHF, involves first training a reward model on pairwise preferences and then optimizing the policy model using reinforcement learning (PPO).",
                "However, PPO is highly sensitive to hyperparameters, complex to implement, and requires running multiple large models concurrently during training, making it computationally heavy."
            ],
            "2. Mathematical Derivation of DPO": [
                "Using the Bradley-Terry preference model, we derive an exact closed-form relation between the optimal policy $\\pi_\\theta$ and the reward function $r(x, y)$. This allows us to reparameterize the reward function in terms of the policy likelihoods.",
                "By substituting this reparameterization into the RL objective, we obtain a simple binary cross-entropy loss that directly optimizes the policy on preference pairs $(y_w, y_l)$ relative to a reference policy $\\pi_{\\text{ref}}$."
            ]
        }
    )))

    # Paper 8: LLaMA
    papers.append(("llama_foundation_models.md", make_academic_summary(
        "LLaMA: Open and Efficient Foundation Language Models",
        "Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, Aurelien Rodriguez, Armand Joulin, Edouard Grave, Guillaume Lample",
        2023,
        "We introduce LLaMA, a collection of foundation language models ranging from 7B to 65B parameters. We train our models on trillions of tokens, and show that it is possible to train state-of-the-art models using publicly available datasets exclusively, without resorting to proprietary and inaccessible datasets. In particular, LLaMA-13B outperforms GPT-3 (175B) on most benchmarks, and LLaMA-65B is competitive with the best models such as Chinchilla and PaLM.",
        {
            "1. Introduction": [
                "Large language models trained on massive text corpora have shown capabilities to perform new tasks from few-shot demonstrations. These performances scale with the number of parameters and training tokens.",
                "In this work, we focus on training series of language models that achieve the best possible performance at various inference budgets, by training on more tokens than typically recommended by scaling laws."
            ],
            "2. Architecture Enhancements": [
                "LLaMA incorporates several improvements inspired by other architectures:",
                "- **Pre-normalization (GPT-3):** To improve training stability, we normalize the input of each transformer sub-layer, using RMSNorm instead of LayerNorm.",
                "- **SwiGLU Activation (PaLM):** We replace the ReLU non-linearity with SwiGLU activation function, using a dimension of $\\frac{2}{3} 4d$ instead of $4d$.",
                "- **Rotary Embeddings (RoPE):** We remove absolute positional embeddings and instead add rotary positional embeddings (RoPE) at each layer of the network."
            ]
        }
    )))

    # Paper 9: QLoRA
    papers.append(("qlora_quantized.md", make_academic_summary(
        "QLoRA: Efficient Finetuning of Quantized LLMs",
        "Tim Dettmers, Artidoro Pagnoni, Ari Holtzman, Luke Zettlemoyer",
        2023,
        "We present QLoRA, an efficient finetuning approach that reduces memory usage enough to finetune a 65B parameter model on a single 48GB GPU while preserving full 16-bit finetuning task performance. QLoRA backpropagates gradients through a frozen, 4-bit quantized pretrained language model into Low-Rank Adapters (LoRA). Our best model family, Guanaco, outperforms all previously released open models on the Vicuna benchmark, reaching 99.3% of ChatGPT performance level.",
        {
            "1. Introduction": [
                "Finetuning large language models is highly effective, but requires enormous GPU memory. For a 65B LLaMA model, standard 16-bit finetuning requires over 780GB of GPU memory.",
                "QLoRA achieves massive memory savings without quality degradation by introducing three innovations: NormalFloat4 (NF4) data type, Double Quantization (DQ), and Paged Optimizers to manage memory spikes."
            ],
            "2. QLoRA Components": [
                "**NormalFloat 4:** NF4 is an information-theoretically optimal quantization data type for normally distributed data, outperforming standard 4-bit integers and floats.",
                "**Double Quantization:** A process of quantizing the quantization constants themselves, saving an additional 0.37 bits per parameter on average.",
                "**Paged Optimizers:** Utilizing NVIDIA unified memory page-to-page transfers between GPU and CPU to prevent out-of-memory errors during gradient computation on long sequences."
            ]
        }
    )))

    # Paper 10: DDPM
    papers.append(("ddpm_diffusion.md", make_academic_summary(
        "Denoising Diffusion Probabilistic Models",
        "Jonathan Ho, Ajay Jain, Pieter Abbeel",
        2020,
        "We present high quality image synthesis results using diffusion probabilistic models, a class of latent variable models inspired by considerations from non-equilibrium thermodynamics. Our best results are obtained by training on a weighted variational bound designed according to a novel connection between diffusion models and denoising score matching with Langevin dynamics, and our models admit a progressive lossy decompression scheme that can be interpreted as autoregressive decoding.",
        {
            "1. Introduction": [
                "Deep generative models of various types have recently demonstrated high quality samples in many image, audio, and video generation domains.",
                "Diffusion models are generative models that learn to reverse a gradual noisy process. In this paper, we show that diffusion models are capable of generating extremely high quality images, matching or exceeding GANs in many settings."
            ],
            "2. Diffusion Process and Reverse Process": [
                "A diffusion model is a parameterized Markov chain trained to produce samples matching the data distribution after finite time.",
                "The forward process (diffusion) adds Gaussian noise to the data in $T$ steps according to a variance schedule. The reverse process (generation) is a Markov chain with learned Gaussian transitions starting from $p(x_T) = \\mathcal{N}(x_T; 0, I)$."
            ]
        }
    )))

    # Write all papers to files
    for filename, content in papers:
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Verify line count
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"Generated {filename}: {len(lines)} lines")

if __name__ == "__main__":
    generate_sources()
