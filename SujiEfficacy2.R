data <- read.csv(file = "data.csv", header = TRUE);
filteredDiscards <- subset(data,isGenbutsu == 0 & (round == 1 | round == 2));
attach(filteredDiscards);
names(filteredDiscards);

y <- isLoser;
x <- numRyanmanAvailable;

myReg <- glm(y ~ x + isSuji + x:isSuji, family = "binomial");
summary(myReg);

myRegSmall <- glm(y ~ x, family = "binomial");
summary(myRegSmall);

anova(myRegSmall, myReg);



# for proportions
yprop <- rep(NA,15)
xtemp <- seq(4,18,1);
print(xtemp);
print(yprop);

for( i in (4:18))
{
	yprop[i-3] = mean(y[x==i]);
}


#add names here
plot(0:18, obspropsIsSuji, xlim = c(18,4), ylim = c(0,1), 
	main = "Suji efficacy", 
	xlab = "Number of Open Waits", 
	ylab = "loss rate",
	type = "p",
	pch = 16,
	col = "red");


#is suji
#points(0:18, obspropsIsSuji,pch=16,col="red");

#plot(jitter(y,amount = 0.025)~x, xlim = c(18,4), ylim = c(0,1), 
#	main = "Suji efficacy", 
#	xlab = "Number of Open Waits", 
#	ylab = "loss rate");

b0 <- myReg$coef[1];
b1 <- myReg$coef[2];
b2 <- myReg$coef[3];
b3 <- myReg$coef[4];


#
curve(exp(b0 + b1*x)/(1+exp(b0+b1*x)),0,18,add=TRUE, col = "blue");
#
curve(exp((b0+b2) + (b1+b3)*x)/(1+exp((b0+b2) + (b1+b3)*x)),0,18,add=TRUE, col = "red");

obspropsIsSuji <- rep(NA,19)
obspropsNotSuji <- rep(NA,19)
for (i in 1:19){
	obspropsIsSuji[i] <- mean(y[(x==i-1) & (isSuji == 1)]);
	obspropsNotSuji[i] <- mean(y[(x==i-1) & (isSuji == 0)]);
}
#is suji
points(0:18, obspropsIsSuji,pch=16,col="red");

#is not suji
points(0:18, obspropsNotSuji,pch=16,col="blue");




