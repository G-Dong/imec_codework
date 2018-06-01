# calibrate_rf
  This manual is a guidance to calibrate the factor of yaw angle, the radius of turning yaw angle and the turning centre.

1.	An initial point which can form an x-axis parallel line with center point should be find. Intuitively, the x value of this initial point should be the largest when sweeping the yaw angle.
2.	The yaw angle sweep: The position monitor only shows the abs position of a point between fiber tip and the turning center. Thus, only the difference between two different fiber tip positions has the meaning which shows the movement length. In such a case, we need the procedure to find the relative move. 
a.	Align the fiber to the grating coupler.
b.	Change the yaw angle.
c.	Align the fiber again without changing the yaw angle.
Thus, by calculating the difference of two abs positions of two different alignment, we can figure out the difference of (x, y) value when yaw change. Then the yaw angle sweeping can be done by changing the yaw angle. 
3.	The difference of abs position on the monitor page shows he fiber tip moving length. In this case, to get the initial point, we have the following procedure:
a.	Normally the u value of initial point is around 7.27 empirically. To verify this, a yaw sweep from u value around 7.2 to 7.3 with proper resolution should be done. The x value with u equals 7.27 should be largest approximately. 
b.	After finding the approximate initial position, we can find the accurate initial position. The idea is that when the initial position is accurate, the two symmetrical positions with the parallel line (initial point and the turning center) as the symmetry axis should share the same x value. In this case, to find the accurate value of initial point, we should change the yaw angle to the value u1 which should be smaller than 6 and make the alignment. The change the yaw angle to the value u2 which should be larger than 8. It should be noticed that we have the relationship: (u1+u2)/2 = u0, where u0 is the u value of initial position.
c.	After changing the yaw angle again, the x-axis is ‘fixed’ which means it should not be change when doing the alignment. By only changing y-axis, we try the alignment. If the insertion loss is too high, over 15% larger than the original, we should change the u1 and do the step b and c again, until we can make an alignment as good as first alignment.
d.	Then find the u0, which is the u value of initial point. The x and y value of initial point should also be recorded in order to calculate the relative move when changing the yaw angle.
4.	It should be noticed that the x and y value is only validated when the fiber tip maintains the same position on the PA300. When resemble or change the fiber tip, the initial position changes and should be found again. But normally, the initial position will stay in approximately the same position which is around 7.2. 
