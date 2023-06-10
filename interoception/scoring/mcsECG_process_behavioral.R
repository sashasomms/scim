# Sasha Sommerfeldt
# July 2020

# Clear the workspace
rm(list=ls())

# Packages ------------------------------------------------------------------------
library(tidyverse)
library(stats)
library(car)
library(ggplot2)

today='20221220b'
rddir = '../../raw-data/interoception/behavioral/'
ddir = '../../processed-data/interoception'

IDS = read_csv("../../subj_lists/T1_IDs.txt", col_names = F)
exclude_ids = c('')

df = data.frame("ID" = IDS$X1, "bt_t1_intero_chisqP" = NA, 
                "bt_t1_intero_q25" = NA, "bt_t1_intero_q75" = NA, "bt_t1_intero_iqr" = NA, 
                "bt_t1_intero_per0" = NA, "bt_t1_intero_per100" = NA, "bt_t1_intero_per200" = NA, 
                "bt_t1_intero_per300" = NA, "bt_t1_intero_per400" = NA, "bt_t1_intero_per500" = NA, 
                "bt_t1_intero_rAccConf" = NA, "bt_t1_intero_sdConf" = NA, 
                "bt_t1_intero_varianceConf" = NA, "bt_t1_mcsLightTone_chisqP" = NA, 
                "bt_t1_mcsLightTone_q25" = NA, "bt_t1_mcsLightTone_q75" = NA, "bt_t1_mcsLightTone_iqr" = NA, 
                "bt_t1_mcsLightTone_per0" = NA, "bt_t1_mcsLightTone_per100" = NA, "bt_t1_mcsLightTone_per200" = NA, 
                "bt_t1_mcsLightTone_per300" = NA, "bt_t1_mcsLightTone_per400" = NA, "bt_t1_mcsLightTone_per500" = NA, 
                "bt_t1_mcsLightTone_rAccConf" = NA, "bt_t1_mcsLightTone_rAccConfCont" = NA,  
                "bt_t1_mcsLightTone_meanAccCont" = NA, "bt_t1_mcsLightTone_sdAccCont" = NA, "bt_t1_mcsLightTone_varAccCont" = NA, 
                "bt_t1_mcsLightTone_sdConf" = NA, "bt_t1_mcsLightTone_varianceConf" = NA)


for (s in IDS$X1) {
  print(s)
  dfL = data.frame(bt_t1_intero_trialDelay = c(0, 100, 200, 300, 400, 500), bt_t1_intero_percentYes = NA)
  # Calc values of the chisquare test and IQR based on the 1993 Brener paper
  subjFile = paste0(rddir, s,"_t1_MCSinteroception.csv")
  if (file.exists(subjFile) & !(s %in% exclude_ids)) {
    dat = read.csv(subjFile)
    if (nrow(dat) > 30) {
      dat$resp01 = ifelse(dat$response == "s", 1,0)
      dat$trialtype = as.factor(dat$trialDelay)
      mod1=glm(resp01 ~ trialtype, family = "binomial", dat)
      summary(mod1)
      chisq.p = anova(mod1, test="Chisq")$Pr[2]
      
      tab = table(dat$trialDelay, dat$response)
      if (sum(tab[,1]) > 0) {
        cum.dist = cumsum(tab[,2]/sum(tab[,2]))
        vals = c(0, 100, 200, 300, 400, 500)
        interp.cdf = approx(vals, cum.dist, n=500)
        x.25 = interp.cdf$x[which.min(abs(interp.cdf$y-.25))]
        x.75 = interp.cdf$x[which.min(abs(interp.cdf$y-.75))]
        iqr.range = x.75-x.25
        df$bt_t1_intero_chisqP[df$ID == s] = chisq.p
        df$bt_t1_intero_q25[df$ID == s] = x.25
        df$bt_t1_intero_q75[df$ID == s] = x.75
        df$bt_t1_intero_iqr[df$ID == s] = iqr.range
      }
      if (sum(tab[,1]) == 0) {
        df$bt_t1_intero_chisqP[df$ID == s] = NA
        df$bt_t1_intero_q25[df$ID == s] = NA
        df$bt_t1_intero_q75[df$ID == s] = NA
        df$bt_t1_intero_iqr[df$ID == s] = NA
      }
      
      # Percents
      nYesTotal = sum(dat$resp01 == 1, na.rm = TRUE)
      nYes0 = sum(dat$trialDelay == 0 & dat$resp01 == 1, na.rm = TRUE)
      nYes100 = sum(dat$trialDelay == 100 & dat$resp01 == 1, na.rm = TRUE)
      nYes200 = sum(dat$trialDelay == 200 & dat$resp01 == 1, na.rm = TRUE)
      nYes300 = sum(dat$trialDelay == 300 & dat$resp01 == 1, na.rm = TRUE)
      nYes400 = sum(dat$trialDelay == 400 & dat$resp01 == 1, na.rm = TRUE)
      nYes500 = sum(dat$trialDelay == 500 & dat$resp01 == 1, na.rm = TRUE)
      
      df$bt_t1_intero_per0[df$ID == s] = nYes0 / nYesTotal
      df$bt_t1_intero_per100[df$ID == s] = nYes100 / nYesTotal
      df$bt_t1_intero_per200[df$ID == s] = nYes200 / nYesTotal
      df$bt_t1_intero_per300[df$ID == s] = nYes300 / nYesTotal
      df$bt_t1_intero_per400[df$ID == s] = nYes400 / nYesTotal
      df$bt_t1_intero_per500[df$ID == s] = nYes500 / nYesTotal
      
      dfL$bt_t1_intero_percentYes[dfL$bt_t1_intero_trialDelay == 0] = nYes0 / nYesTotal
      dfL$bt_t1_intero_percentYes[dfL$bt_t1_intero_trialDelay == 100] = nYes100 / nYesTotal
      dfL$bt_t1_intero_percentYes[dfL$bt_t1_intero_trialDelay == 200] = nYes200 / nYesTotal
      dfL$bt_t1_intero_percentYes[dfL$bt_t1_intero_trialDelay == 300] = nYes300 / nYesTotal
      dfL$bt_t1_intero_percentYes[dfL$bt_t1_intero_trialDelay == 400] = nYes400 / nYesTotal
      dfL$bt_t1_intero_percentYes[dfL$bt_t1_intero_trialDelay == 500] = nYes500 / nYesTotal
      
      ## What delay did they most frequently rate as simultaneous?
      highest_percent = dfL[order(dfL$bt_t1_intero_percentYes, decreasing = TRUE), ][1,2]
      # Did they rate 2 at the same frequency?
      if (highest_percent %in% dfL[order(dfL$bt_t1_intero_percentYes), ][2:6,2]) {
        favDelays = dfL$bt_t1_intero_trialDelay[dfL$bt_t1_intero_percentYes == highest_percent]
        n = length(favDelays)
        if (n == 2) {
          favDelay = paste(favDelays[1], favDelays[2], sep = "_")
          df$bt_t1_intero_favDelays[df$ID == s] = favDelay
        }
        if (n == 3) {
          favDelay = paste(favDelays[1], favDelays[2], favDelays[3], sep = "_")
          df$bt_t1_intero_favDelays[df$ID == s] = favDelay
        }
        if (n == 4) {
          favDelay = paste(favDelays[1], favDelays[2], favDelays[3], favDelays[4], sep = "_")
          df$bt_t1_intero_favDelays[df$ID == s] = favDelay
        }
      }
      if (n == 1) {
        favDelay = dfL$bt_t1_intero_trialDelay[dfL$bt_t1_intero_percentYes == highest_percent]
        df$bt_t1_intero_favDelay[df$ID == s] = favDelay
        
        ## Insight calc 
        # Accuracy calculation for heartbeat-tone insight:
        # Favorite delay and said simultaneous = accurate
        dat$accuracy[(dat$trialDelay == favDelay) & (dat$resp01 == 1)] = 1
        # Favorite delay and said not-simultaneous = inaccurate
        dat$accuracy[(dat$trialDelay == favDelay) & (dat$resp01 == 0)] = 0
        # Other delay and said simultaneous = inaccurate
        dat$accuracy[dat$trialDelay != favDelay & (dat$resp01 == 1)] = 0
        # Other delay and said not simultaneous = accurate
        dat$accuracy[dat$trialDelay != favDelay & (dat$resp01 == 0)] = 1
        
        # Need variance in responses to compute metrics
        df$bt_t1_intero_sdConf[df$ID == s] = sd(dat$confidence, na.rm = T)
        df$bt_t1_intero_varianceConf[df$ID == s] = var(dat$confidence, na.rm = T)
        if (df$bt_t1_intero_varianceConf[df$ID == s] > 0) {
          df$bt_t1_intero_rAccConf[df$ID == s] = cor(dat$confidence, dat$accuracy)
        }
        if (df$bt_t1_intero_varianceConf[df$ID == s] == 0) {
          df$bt_t1_intero_rAccConf[df$ID == s] = NA
          print(paste0(s, " had no variance in confidence."))
        }
      }
      
    
      ## Plot the distribution for each subject
      pdf(paste(ddir,"/participant_plots/",s,"_percents_",today,".pdf",sep=''))
      PercentsPlot = ggplot(dfL, aes(x=bt_t1_intero_trialDelay, y=bt_t1_intero_percentYes)) +
        ggtitle(s)+
        geom_bar(stat="identity",fill='#F1C40F') +
        #geom_point(stat="identity", shape=1, size=1.5, alpha=.7, position="jitter")  +
        labs(x="Delay Condition", y="% Simultaneous Judgements") +
        theme_bw() +
        theme(panel.grid.minor = element_blank(), 
              axis.title=element_text(size=16), 
              plot.title=element_text(size=16, hjust=.5), 
              axis.text=element_text(size=16)) +
        scale_x_continuous(breaks = seq(0, 500, by = 100), limits = c(-100, 600)) +
        scale_y_continuous(breaks = seq(0, .6, by = .1), limits = c(0, .6)) +
        theme(legend.position="none")
      print(PercentsPlot)
      dev.off() # Finish PDF with subject plots
    
      
      # reset everything
      chisq.p = NA
      x.25 = NA
      x.75 = NA
      iqr.range = NA
      nYes0 = NA
      nYes100 = NA
      nYes200 = NA
      nYes300 = NA
      nYes400 = NA
      nYes500 = NA
      nYesTotal = NA
      favDelay = NA
      favDelays = NA
    } # end nrow if
    if (nrow(dat) < 30) {
      print(paste(subjFile, " has less than 30 rows"))
    }
  } # end file exists if
} # end subj loop

hist(df$bt_t1_intero_iqr, main='Inter-Quartile Range (IQR) Values Across the Sample', xlab='IQR', 
     ylab="Number of Participants", col='#9A1705', cex.axis=1.7, cex.main=1.6)

hist(as.numeric(df$bt_t1_intero_favDelay[3:18]), main='Delay most frequently rated as simultaneous \n(heartbeat trials)', 
     xlab='Delay', ylab="Number of Participants", col='#9A1705', cex.axis=1.7, cex.main=1.6)

hist(df$bt_t1_intero_rAccConf, main='Accuracy-Confidence Correspondence \n(heartbeat trials)', 
     xlab='Accuracy x Confidence (r)', ylab="Number of Participants", col='#9A1705', cex.axis=1.7, cex.main=1.6)
table(df$bt_t1_intero_rAccConf, useNA = "ifany")



table(df$bt_t1_intero_favDelay, useNA = "ifany")


# LIGHT-TONE TRIALS ------------------------------------------------------------

for (s in IDS$X1) {
  print(s)
  dfL = data.frame(bt_t1_mcsLightTone_trialDelay = c(0, 100, 200, 300, 400, 500), bt_t1_mcsLightTone_percentYes = NA)
  subjFile = paste0(rddir, s, "_t1_MCSinteroception_lightTone.csv")
  if (file.exists(subjFile)) {
    dat = read.csv(subjFile)
    if (nrow(dat) > 24) {
      dat$resp01 = ifelse(dat$response == "s", 1,0)
      dat$trialtype = as.factor(dat$trialDelay)
      mod1=glm(resp01 ~ trialtype, family = "binomial", dat)
      summary(mod1)
      chisq.p = anova(mod1, test="Chisq")$Pr[2]
      
      # Need variance in responses to compute metrics
      tab = table(dat$trialDelay, dat$response)
      if (sum(tab[,1]) > 0 & sum(tab[,1]) != 30) {
        cum.dist = cumsum(tab[,2]/sum(tab[,2]))
        vals = c(0, 100, 200, 300, 400, 500)
        interp.cdf = approx(vals, cum.dist, n=500)
        x.25 = interp.cdf$x[which.min(abs(interp.cdf$y-.25))]
        x.75 = interp.cdf$x[which.min(abs(interp.cdf$y-.75))]
        iqr.range = x.75-x.25
        df$bt_t1_mcsLightTone_chisqP[df$ID == s] = chisq.p
        df$bt_t1_mcsLightTone_q25[df$ID == s] = x.25
        df$bt_t1_mcsLightTone_q75[df$ID == s] = x.75
        df$bt_t1_mcsLightTone_iqr[df$ID == s] = iqr.range
      }
      if (sum(tab[,1]) == 0 | sum(tab[,1]) == 30) {
        df$bt_t1_mcsLightTone_chisqP[df$ID == s] = NA
        df$bt_t1_mcsLightTone_q25[df$ID == s] = NA
        df$bt_t1_mcsLightTone_q75[df$ID == s] = NA
        df$bt_t1_mcsLightTone_iqr[df$ID == s] = NA
        print(paste0(s, " had no variance in responses for lightTone."))
      }

      
      # Percents
      nYesTotal = sum(dat$resp01 == 1, na.rm = TRUE)
      nYes0 = sum(dat$trialDelay == 0 & dat$resp01 == 1, na.rm = TRUE)
      nYes100 = sum(dat$trialDelay == 100 & dat$resp01 == 1, na.rm = TRUE)
      nYes200 = sum(dat$trialDelay == 200 & dat$resp01 == 1, na.rm = TRUE)
      nYes300 = sum(dat$trialDelay == 300 & dat$resp01 == 1, na.rm = TRUE)
      nYes400 = sum(dat$trialDelay == 400 & dat$resp01 == 1, na.rm = TRUE)
      nYes500 = sum(dat$trialDelay == 500 & dat$resp01 == 1, na.rm = TRUE)
      
      df$bt_t1_mcsLightTone_per0[df$ID == s] = nYes0 / nYesTotal
      df$bt_t1_mcsLightTone_per100[df$ID == s] = nYes100 / nYesTotal
      df$bt_t1_mcsLightTone_per200[df$ID == s] = nYes200 / nYesTotal
      df$bt_t1_mcsLightTone_per300[df$ID == s] = nYes300 / nYesTotal
      df$bt_t1_mcsLightTone_per400[df$ID == s] = nYes400 / nYesTotal
      df$bt_t1_mcsLightTone_per500[df$ID == s] = nYes500 / nYesTotal
      
      dfL$bt_t1_mcsLightTone_percentYes[dfL$bt_t1_mcsLightTone_trialDelay == 0] = nYes0 / nYesTotal
      dfL$bt_t1_mcsLightTone_percentYes[dfL$bt_t1_mcsLightTone_trialDelay == 100] = nYes100 / nYesTotal
      dfL$bt_t1_mcsLightTone_percentYes[dfL$bt_t1_mcsLightTone_trialDelay == 200] = nYes200 / nYesTotal
      dfL$bt_t1_mcsLightTone_percentYes[dfL$bt_t1_mcsLightTone_trialDelay == 300] = nYes300 / nYesTotal
      dfL$bt_t1_mcsLightTone_percentYes[dfL$bt_t1_mcsLightTone_trialDelay == 400] = nYes400 / nYesTotal
      dfL$bt_t1_mcsLightTone_percentYes[dfL$bt_t1_mcsLightTone_trialDelay == 500] = nYes500 / nYesTotal
      
      ## What delay did they most frequently rate as simultaneous?
      highest_percent = dfL[order(dfL$bt_t1_mcsLightTone_percentYes, decreasing = TRUE), ][1,2]
      print(dfL[order(dfL$bt_t1_mcsLightTone_percentYes, decreasing = TRUE), ])
      # Did they rate 2 at the same frequency?
      if (highest_percent %in% dfL[order(dfL$bt_t1_mcsLightTone_percentYes), ][2:6,2]) {
        favDelays = dfL$bt_t1_mcsLightTone_trialDelay[dfL$bt_t1_mcsLightTone_percentYes == highest_percent]
        print(paste0("Favorite delays are: ", favDelays))
        n = length(favDelays)
        if (n == 2) {
          favDelay = paste(favDelays[1], favDelays[2], sep = "_")
          df$bt_t1_mcsLightTone_favDelays[df$ID == s] = favDelay
        }
        if (n == 3) {
          favDelay = paste(favDelays[1], favDelays[2], favDelays[3], sep = "_")
          df$bt_t1_mcsLightTone_favDelays[df$ID == s] = favDelay
        }
        if (n == 4) {
          favDelay = paste(favDelays[1], favDelays[2], favDelays[3], favDelays[4], sep = "_")
          df$bt_t1_mcsLightTone_favDelays[df$ID == s] = favDelay
        }
      }
      if (n == 1) {
        favDelay = dfL$bt_t1_mcsLightTone_trialDelay[dfL$bt_t1_mcsLightTone_percentYes == highest_percent]
        df$bt_t1_mcsLightTone_favDelay[df$ID == s] = favDelay
        df$bt_t1_mcsLightTone_favDelays[df$ID == s] = favDelay
      }
    
      ## Insight calc s
      # Need variance in responses to compute metrics
      df$bt_t1_mcsLightTone_sdConf[df$ID == s] = sd(dat$confidence, na.rm = T)
      df$bt_t1_mcsLightTone_varianceConf[df$ID == s] = var(dat$confidence, na.rm = T)
      
      # Accuracy calculation for light-tone insight:
      # Continuous
      # 0 ms delay and said simultaneous = accurate level 6
      dat$accuracy_cont[(dat$trialDelay == 0) & (dat$resp01 == 1)] = 6
      # 0 ms delay and said not-simultaneous = accurate level 1
      dat$accuracy_cont[(dat$trialDelay == 0) & (dat$resp01 == 0)] = 1
      # 100 ms delay and said simultaneous = accurate level 5
      dat$accuracy_cont[(dat$trialDelay == 100) & (dat$resp01 == 1)] = 5
      # 100 ms delay and said not simultaneous = accurate level 2
      dat$accuracy_cont[(dat$trialDelay == 100) & (dat$resp01 == 0)] = 2
      # 200 ms delay and said simultaneous = accurate level 4
      dat$accuracy_cont[(dat$trialDelay == 200) & (dat$resp01 == 1)] = 4
      # 200 ms delay and said not simultaneous = accurate level 3
      dat$accuracy_cont[(dat$trialDelay == 200) & (dat$resp01 == 0)] = 3
      # 300 ms delay and said simultaneous = accurate level 3
      dat$accuracy_cont[(dat$trialDelay == 300) & (dat$resp01 == 1)] = 3
      # 300 ms delay and said not simultaneous = accurate level 4
      dat$accuracy_cont[(dat$trialDelay == 300) & (dat$resp01 == 0)] = 4
      # 400 ms delay and said simultaneous = accurate level 2
      dat$accuracy_cont[(dat$trialDelay == 400) & (dat$resp01 == 1)] = 2
      # 400 ms delay and said not simultaneous = accurate level 5
      dat$accuracy_cont[(dat$trialDelay == 400) & (dat$resp01 == 0)] = 5
      # 500 ms delay and said simultaneous = accurate level 1
      dat$accuracy_cont[(dat$trialDelay == 500) & (dat$resp01 == 1)] = 1
      # 500 ms delay and said not simultaneous = accurate level 6
      dat$accuracy_cont[(dat$trialDelay == 500) & (dat$resp01 == 0)] = 6
      
      # Dichotomous accuracy
      # 0 ms delay and said simultaneous = accurate
      dat$accuracy[(dat$trialDelay == 0) & (dat$resp01 == 1)] = 1
      # 0 ms delay and said not-simultaneous = inaccurate
      dat$accuracy[(dat$trialDelay == 0) & (dat$resp01 == 0)] = 0
      # 100 ms delay and said simultaneous = inaccurate
      dat$accuracy[(dat$trialDelay == 100) & (dat$resp01 == 1)] = 0
      # 100 ms delay and said not simultaneous = accurate
      dat$accuracy[(dat$trialDelay == 100) & (dat$resp01 == 0)] = 1
      # 200 ms delay and said simultaneous = inaccurate
      dat$accuracy[(dat$trialDelay == 200) & (dat$resp01 == 1)] = 0
      # 200 ms delay and said not simultaneous = accurate
      dat$accuracy[(dat$trialDelay == 200) & (dat$resp01 == 0)] = 1
      # 300 ms delay and said simultaneous = inaccurate
      dat$accuracy[(dat$trialDelay == 300) & (dat$resp01 == 1)] = 0
      # 300 ms delay and said not simultaneous = accurate
      dat$accuracy[(dat$trialDelay == 300) & (dat$resp01 == 0)] = 1
      # 400 ms delay and said simultaneous = inaccurate
      dat$accuracy[(dat$trialDelay == 400) & (dat$resp01 == 1)] = 0
      # 400 ms delay and said not simultaneous = accurate
      dat$accuracy[(dat$trialDelay == 400) & (dat$resp01 == 0)] = 1
      # 500 ms delay and said simultaneous = inaccurate
      dat$accuracy[(dat$trialDelay == 500) & (dat$resp01 == 1)] = 0
      # 500 ms delay and said not simultaneous = accurate
      dat$accuracy[(dat$trialDelay == 500) & (dat$resp01 == 0)] = 1
      
      # Mean and sd of accuracy
      df$bt_t1_mcsLightTone_meanAccCont[df$ID == s] = mean(dat$accuracy_cont, na.rm = T)
      df$bt_t1_mcsLightTone_sdAccCont[df$ID == s] = sd(dat$accuracy_cont, na.rm = T)
      df$bt_t1_mcsLightTone_varAccCont[df$ID == s] = var(dat$accuracy_cont, na.rm = T)
      
      
      if (df$bt_t1_mcsLightTone_varianceConf[df$ID == s] > 0) {
        df$bt_t1_mcsLightTone_rAccConf[df$ID == s] = cor(dat$confidence, dat$accuracy)
        df$bt_t1_mcsLightTone_rAccConfCont[df$ID == s] = cor(dat$confidence, dat$accuracy_cont)
      }
      if (df$bt_t1_mcsLightTone_varianceConf[df$ID == s] == 0) {
        df$bt_t1_mcsLightTone_rAccConf[df$ID == s] = NA
        df$bt_t1_mcsLightTone_rAccConf_cont[df$ID == s] = NA
        print(paste0(s, " had no variance in confidence for lightTone."))
      }
  
      ## Plot the distribution for each subject
      pdf(paste(ddir,"/participant_plots/",s,"_lightTone_percents_",today,".pdf",sep=''))
      PercentsPlot = ggplot(dfL, aes(x=bt_t1_mcsLightTone_trialDelay, y=bt_t1_mcsLightTone_percentYes)) +
        ggtitle(paste(s, "LightTone")) +
        geom_bar(stat="identity",fill='#4CBB17') +
        #geom_point(stat="identity", shape=1, size=1.5, alpha=.7, position="jitter")  +
        labs(x="Delay Condition", y="% Simultaneous Judgements") +
        theme_bw() +
        theme(panel.grid.minor = element_blank(), 
              axis.title=element_text(size=16), 
              plot.title=element_text(size=16, hjust=.5), 
              axis.text=element_text(size=16)) +
        scale_x_continuous(breaks = seq(0, 500, by = 100), limits = c(-100, 600)) +
        scale_y_continuous(breaks = seq(0, .6, by = .1), limits = c(0, .6)) +
        theme(legend.position="none")
      print(PercentsPlot)
      dev.off() # Finish PDF with subject plots
      
      # reset everything
      chisq.p = NA
      x.25 = NA
      x.75 = NA
      iqr.range = NA
      nYes0 = NA
      nYes100 = NA
      nYes200 = NA
      nYes300 = NA
      nYes400 = NA
      nYes500 = NA
      nYesTotal = NA
      favDelay = NA
      favDelays = NA
    }
  }
}


hist(df$bt_t1_mcsLightTone_iqr, main='Inter-Quartile Range (IQR) Values Across the Sample', 
     xlab='IQR', ylab="Number of Participants", col='#4CBB17', cex.axis=1.7, cex.main=1.6)

hist(as.numeric(df$bt_t1_mcsLightTone_favDelay), main='Delay most frequently rated as simultaneous \n(Light-tone trials)', 
     xlab='Delay', ylab="Number of Participants", col='#4CBB17', cex.axis=1.7, cex.main=1.6)

hist(df$bt_t1_mcsLightTone_rAccConf, main='Accuracy-Confidence Correspondence \n(Light-tone trials)', 
     xlab='Accuracy x Confidence (r)', ylab="Number of Participants", col='#4CBB17', cex.axis=1.7, cex.main=1.6)

hist(df$bt_t1_mcsLightTone_rAccConf_cont, main='Accuracy_cont-Confidence Correspondence \n(Light-tone trials)', 
     xlab='Accuracy x Confidence (r)', ylab="Number of Participants", col='#4CBB17', cex.axis=1.7, cex.main=1.6)


table(df$bt_t1_mcsLightTone_favDelay, useNA = "ifany")
table(df$bt_t1_mcsLightTone_favDelays, useNA = "ifany")



# Write out the file ----------------------------------------------------------
fnameW = paste("bt_t1_mcs_", today, ".csv", sep = '')
fpathW = paste(ddir, "/", fnameW, sep='')
write.csv(df, file = fpathW)