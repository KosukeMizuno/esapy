---
title: "Untitled-9"
category: Users/kosuke-mizuno
tags: 
created_at: 2020-05-03T21:46:39+09:00
updated_at: 2020-05-03T21:46:39+09:00
published: false
number: 456
---

次の公式を示す。

$$e^A B e^{-A} = B + [A,B] + \frac{1}{2}[A, [A,B]] + \cdots$$

次の関数をTaylor展開することで示せる。

$$f(t) = e^{tA} B e^{-tA}$$

まず、一回微分 $f'(t)$、二階微分 $f''(t)$ は

$$\begin{aligned}
f'(t) &= A e^{tA} B e^{-tA} - e^{tA} B A e^{-tA} \cr
  &= e^{tA} A B e^{-tA} - e^{tA} B A e^{-tA} \quad\because [e^{tA}, A] =0 \cr
  &= e^{tA} (AB-BA) e^{-tA} \cr
  &= e^{tA} [A,B] e^{-tA}\end{aligned}$$

$$\begin{aligned}
f''(t) &= e^{tA} A [A,B] e^{-tA} - e^{tA} [A,B] A e^{-tA} \cr
  &= e^{tA} (A [A,B] - [A,B] A) e^{-tA} \cr
  &= e^{tA} [A, [A,B]] e^{-tA}\end{aligned}$$

である。

ここで、交換子を $[A,B] = \mathrm{ad}_A [B]$
と書くことにし、さらに次のように約束する。

$$\begin{aligned}
\mathrm{ad}_A^0 [B] &= B \cr
\mathrm{ad}_A^1 [B] &= \mathrm{ad}_A [B] = [A,B] \cr
\mathrm{ad}_A^2 [B] &= \mathrm{ad}_A [\mathrm{ad}_A [B]] = [A, [A, B]] \cr
&\vdots \cr
\mathrm{ad}_A^n [B] &= \underbrace{[A,[A,\ldots,[A}_n,B]]\cdots]\end{aligned}$$

この表記法を用いると、$f'(t) = e^{tA}\\,\mathrm{ad}_A^1 [B] \\,e^{-tA}$,
$f''(t) = e^{tA} \\,\mathrm{ad}_A^2 [B] \\,e^{-tA}$
となる。これを一般化する。

$$\begin{aligned}
\frac{d}{dt} \left( e^{tA} \,\mathrm{ad}_A^n[B]\,e^{-tA} \right) &= e^{tA} A\,\mathrm{ad}_A^n[B]\, e^{-tA} - e^{tA} \,\mathrm{ad}_A^n[B]\, A e^{-tA} \cr
  &= e^{tA} \left( A\,\mathrm{ad}_A^n[B]- \mathrm{ad}_A^n[B]\,A \right) e^{-tA} \cr
  &= e^{tA} \left[ A, \mathrm{ad}_A^n[B] \right] e^{-tA} \cr
  &= e^{tA}\,\mathrm{ad}_A^{n+1}[B]\,e^{-tA}\end{aligned}$$

以上より、

$$f^{(n)}(t) = e^{tA} \,\mathrm{ad}_A^n[B]\,e^{-tA}$$

が得られた。$t=0$ では $f^{(n)}(0) = \mathrm{ad}_A^n[B]$ である。$f(t)$
のTaylor展開により、

$$\begin{aligned}
f(t) &= \sum_{n=0}^\infty \frac{1}{n!} f^{(n)}(0) \, t^n \cr
  &= \sum_{n=0}^\infty \frac{1}{n!} \mathrm{ad}_A^n[B]\,t^n\end{aligned}$$

以上より、

$$f(0) = e^{A} B e^{-A} = \sum_{n=0}^\infty \frac{1}{n!} \mathrm{ad}_A^n[B] = B + [A,B] + \frac{1}{2}[A, [A,B]] + \cdots$$

を示すことができた。

次のように書くこともできる。

$$e^{A} B e^{-A} = e^{\mathrm{ad}_A [\cdot]} B$$

定義から明らかに、超演算子 $\mathrm{ad}_A[\cdot]$ は線形演算子である。

$$\begin{aligned}
\mathrm{ad}_A^n[B+C] &= [A,[A,\cdots,[A,B+C]\cdots] \cr
  &= [A,[A,\cdots,[A,B]\cdots] + [A,[A,\cdots,[A,C]\cdots] \cr
  &= \mathrm{ad}_A^n[B] + \mathrm{ad}_A^n[C]\end{aligned}$$

演算子 $A$ が Normal operator
だと仮定すると、次のように固有値分解できる。

$$A = \sum_k \lambda_k \ket{k}\!\!\bra{k}$$

この時、演算子 $\ket{i}\\!\\!\bra{j}$ は超演算子 $\mathrm{ad}_A[\cdot]$
の固有値である。

$$\begin{aligned}
\mathrm{ad}_A\left[\ket{i}\!\!\bra{j}\right] &= [A, \ket{i}\!\!\bra{j}] \cr
  &= \left(\sum_k \lambda_k \ket{k}\!\!\bra{k}\right) \ket{i}\!\!\bra{j} - \ket{i}\!\!\bra{j} \left( \sum_k \lambda_k \ket{k}\!\!\bra{k} \right) \cr
  &= (\lambda_i - \lambda_j) \ket{i}\!\!\bra{j}\end{aligned}$$

よって、$A$ の同じ固有値に属する固有ベクトル $\ket{i}$, $\ket{j}$
について、$\ket{i}\\!\\!\bra{j}$ は
$\mathrm{ad}_A[\ket{i}\\!\\!\bra{j}]$ の固有演算子であり、固有値はゼロ。
$\ket{i}$, $\ket{j}$ が $A$
の異なる固有空間に属する場合、$\ket{i}\\!\\!\bra{j}$ の固有値は
$\lambda_i - \lambda_j$ である。

また次も成り立つ。

$$\mathrm{ad}_A^n\left[\ket{i}\!\!\bra{j}\right] = (\lambda_i - \lambda_j)^n \ket{i}\!\!\bra{j}$$

同様の議論から、超演算子 $\mathcal{I}_A[B] = e^A B e^{-A}$
を定義するとこれも線形演算子であり、$\ket{i}\\!\\!\bra{j}$ は固有値
$e^{\lambda_i - \lambda_j}$ に属する固有演算子である。

シュレディンガー表示からハイゼンベルク表示（もしくは相互作用表示）への移行を考えると、
シュレディンガー表示で演算子 $A$ はハイゼンベルク表示で
$A(t) = e^{iH_0t} A e^{-iH_0t}$ であるから、

$$A(t) = A + (it) [A,H_0] + \frac{(it)^2}{2!} [A, [A, H_0]] + \frac{(it)^3}{3!} [A, [A, [A, H_0]]] + \cdots$$

ここで、演算子 $\ket{i}\\!\\!\bra{j}$ が固有演算子であることを用いると

$$\begin{aligned}
e^A \ket{i}\!\!\bra{j} e^{-A} &= e^{\mathrm{ad}_A[\cdot]} \ket{i}\!\!\bra{j} \cr
  &= \sum_{n=0}^\infty \frac{1}{n!}\mathrm{ad}_A^n[\ket{i}\!\!\bra{j}] \cr
  &= \sum_{n=0}^\infty \frac{1}{n!} (\lambda_i - \lambda_j)^n \ket{i}\!\!\bra{j}\cr
  &= e^{\lambda_i - \lambda_j} \ket{i}\!\!\bra{j}\end{aligned}$$

である。

$A \to i H_0 t$ と置き換えると、摂動ハミルトニアン
$H_1 = [h_{ij}]_{i,j}$ の相互作用表示 $H_1^I(t)$ は

$$H_1^I(t) = e^{iH_0t} H_1 e^{-iH_0t} = \sum_{i,j} e^{i(\epsilon_i - \epsilon_j)t} h_{ij} \ket{i}\!\!\bra{j}$$

となり、[実験マニュアル・基礎理論/基礎理論/回転座標変換と相互作用表示
\#量子力学 -
dia-pe-titech.esa.io](https://dia-pe-titech.esa.io/posts/406)
と同様の表式が得られた。
注）今の所リンク先と符号が違うけど、向こうの記事が間違ってる…

また、エルミート演算子 $K$ としてユニタリ演算子 $U=\exp(iK)$
によるユニタリ変換$A' = UAU^\dagger$ を考えてみる。$K$
の固有値は全て実数であるから、$iK$ の固有値は全て純虚数。全ての $i$, $j$
について $|e^{\lambda_i - \lambda_j}|=1$
より、ユニタリ変換は行列要素の大きさを変えず、位相だけを変化させることがわかる。

-   おもったより面白くてキレイな関係が得られた。

-   指数関数で挟む＝交換子を指数的に適用する　という対応ができる。

-   交換子を $\mathrm{ad}$
    で表記するのはどこかで見たやり方だけど、一般的に通じるものではないと思う
