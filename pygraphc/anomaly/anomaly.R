# example of outlier detection based on fitting of some data distribution models
library(fitdistrplus)
library(extremevalues)

# load data
data("groundbeef", package = "fitdistrplus")

# fit to distribution model
fln <- fitdist(groundbeef$serving, "lnorm")
fexp <- fitdist(groundbeef$serving, "exp")
fw <- fitdist(groundbeef$serving, "weibull")
fn <- fitdist(groundbeef$serving, "norm")

# plot
plot.legend <- c("lognormal", "exponential", "weibull", "normal")
denscomp(list(fln, fexp, fw, fn), legendtext = plot.legend)

# get goodness of fit. at the moment, we only consider Aikake's Information Criterion (aic) measurement
g <- gofstat(list(fln, fexp, fw, fn), fitnames = c("lognormal", "exponential", "weibull", "normal"))
final_distribution <- rownames(as.matrix(sort(g$aic)[1]))

# get outlier
outlier1 <- getOutliers(groundbeef$serving, method="I", distribution=final_distribution)
outlier2 <- getOutliers(groundbeef$serving, method="II", distribution=final_distribution)
outlierPlot(groundbeef$serving, outlier1, mode="qq")
outlierPlot(groundbeef$serving, outlier2, mode="residual")